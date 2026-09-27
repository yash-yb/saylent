"""
Seeds a realistic demo dataset: 1 nation (India, extendable to other BRICS
members by adding rows), 4 states, 10 districts, ~30 PHCs, 8 medicines, and
60 days of daily consumption/bed/attendance history per PHC with deliberate
trend + noise so the forecasting and redistribution engines have something
real to chew on (some PHCs trending up towards stockout, some flat, some
with surplus).
"""
import random
from datetime import date, timedelta
from .database import Base, engine, SessionLocal
from . import models as m

random.seed(42)

STATES_DISTRICTS = {
    "Maharashtra": ["Pune", "Nagpur", "Nashik"],
    "Uttar Pradesh": ["Lucknow", "Varanasi", "Kanpur"],
    "Karnataka": ["Bengaluru Rural", "Belagavi"],
    "Bihar": ["Patna", "Gaya"],
}

MEDICINES = [
    ("Paracetamol 500mg", "strips", 5, False),
    ("ORS Sachets", "sachets", 3, True),
    ("Amoxicillin 250mg", "strips", 7, True),
    ("Iron-Folic Acid Tablets", "strips", 10, False),
    ("Anti-Malarial (ACT)", "kits", 5, True),
    ("Insulin Vials", "vials", 5, True),
    ("Measles-Rubella Vaccine", "vials", 3, True),
    ("IV Fluids (Ringer's Lactate)", "bottles", 7, True),
]

PHC_PROFILES = ["rising_demand", "falling_demand", "flat", "spiking", "surplus_heavy"]


def run_seed():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    nation = m.Nation(name="India", code="IN")
    db.add(nation)
    db.flush()

    medicine_objs = {}
    for name, unit, lead, critical in MEDICINES:
        med = m.Medicine(name=name, unit=unit, procurement_lead_time_days=lead, critical=critical)
        db.add(med)
        db.flush()
        medicine_objs[name] = med

    phc_id_counter = 1
    all_phcs = []

    for state_name, districts in STATES_DISTRICTS.items():
        state = m.State(name=state_name, nation_id=nation.id)
        db.add(state)
        db.flush()

        for district_name in districts:
            district = m.District(name=district_name, state_id=state.id,
                                   population=random.randint(400_000, 2_500_000))
            db.add(district)
            db.flush()

            n_phcs = random.randint(2, 4)
            for i in range(n_phcs):
                profile = random.choice(PHC_PROFILES)
                total_beds = random.choice([15, 20, 30])
                phc = m.PHC(
                    name=f"{district_name} PHC-{i+1}",
                    district_id=district.id,
                    lat=round(random.uniform(15.0, 28.0), 4),
                    lng=str(round(random.uniform(72.0, 88.0), 4)),
                    total_beds=total_beds,
                )
                db.add(phc)
                db.flush()
                all_phcs.append((phc, profile))
                phc_id_counter += 1

    db.commit()

    # --- Time series history: 60 days ---
    today = date.today()
    start = today - timedelta(days=60)

    for phc, profile in all_phcs:
        for med_name, unit, lead, critical in MEDICINES:
            med = medicine_objs[med_name]
            base = random.uniform(4, 15) if not critical else random.uniform(2, 8)

            if profile == "rising_demand":
                daily_trend = random.uniform(0.15, 0.4)
            elif profile == "falling_demand":
                daily_trend = random.uniform(-0.3, -0.05)
            elif profile == "spiking":
                daily_trend = random.uniform(0.05, 0.1)
            else:
                daily_trend = random.uniform(-0.05, 0.05)

            qty_dispensed_series = []
            for d in range(60):
                noise = random.gauss(0, base * 0.15)
                spike = 0
                if profile == "spiking" and d > 45 and random.random() < 0.3:
                    spike = base * random.uniform(1.5, 3.0)
                value = max(0, base + daily_trend * d + noise + spike)
                qty_dispensed_series.append(round(value, 1))
                db.add(m.ConsumptionLog(
                    phc_id=phc.id, medicine_id=med.id,
                    date=start + timedelta(days=d),
                    qty_dispensed=value,
                ))

            avg_recent = sum(qty_dispensed_series[-14:]) / 14
            if profile == "surplus_heavy":
                current_qty = avg_recent * random.uniform(18, 30)
            elif profile in ("rising_demand", "spiking"):
                current_qty = avg_recent * random.uniform(3, 6)
            else:
                current_qty = avg_recent * random.uniform(8, 14)

            db.add(m.MedicineStock(
                phc_id=phc.id, medicine_id=med.id,
                current_qty=round(current_qty, 1),
                reorder_level=round(avg_recent * lead, 1),
            ))

        # bed occupancy history (just today's snapshot needed for demo)
        occ_ratio = random.uniform(0.5, 0.95)
        db.add(m.BedStatus(phc_id=phc.id, date=today,
                            occupied_beds=int(phc.total_beds * occ_ratio)))

        # personnel attendance snapshot
        for role, total in [("Doctor", random.randint(1, 3)),
                             ("Nurse", random.randint(2, 6)),
                             ("Pharmacist", 1)]:
            present = max(0, total - random.choice([0, 0, 0, 1]))
            db.add(m.PersonnelAttendance(phc_id=phc.id, date=today, role=role,
                                          present=present, total=total))

    db.commit()
    db.close()
    print(f"Seeded {len(all_phcs)} PHCs across {sum(len(v) for v in STATES_DISTRICTS.values())} districts.")


if __name__ == "__main__":
    run_seed()
