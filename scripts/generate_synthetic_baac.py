import os
import random
import logging
import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def generate_synthetic_baac():
    random.seed(42)
    np.random.seed(42)

    out_dir = "/Users/nolll/Documents/car_acc/data/raw"
    prod_dir = "/Users/nolll/Documents/car_acc/data/production_logs"
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(prod_dir, exist_ok=True)

    # VOLUME CIBLE : 300 000 accidents (~6 années)
    num_accidents = 300000

    carac_data = []
    lieux_data = []
    vehic_data = []
    usag_data = []

    years = [2019, 2020, 2021, 2022, 2023, 2024]
    year_weights = [0.10, 0.10, 0.15, 0.15, 0.25, 0.25]

    metropole_deps = [
        "01",
        "13",
        "31",
        "33",
        "34",
        "44",
        "59",
        "69",
        "75",
        "76",
        "77",
        "78",
        "91",
        "92",
        "93",
        "94",
        "95",
        "2A",
        "2B",
    ]
    dom_deps = ["971", "972", "973", "974"]

    adresses = [
        "Rue de Paris",
        "Avenue Jean Jaurès",
        "Boulevard Victor Hugo",
        "Route Nationale",
        "Chemin des Vignes",
        "Rue de la République",
        "Place de la Gare",
        "Avenue de Gaulle",
        "Rue Pasteur",
        "Route de Lyon",
        "Boulevard de la Liberté",
        "Avenue Leclerc",
        "Rue Gambetta",
        "Chemin du Moulin",
        "Rue des Fleurs",
        "Route de Toulouse",
        "Avenue de la Mer",
        "Rue Saint-Jean",
        "Place de la Mairie",
        "Boulevard Pasteur",
    ]

    logging.info(f"Generating {num_accidents} accidents...")

    # Pre-generate some random arrays to speed up the loop
    ans = random.choices(years, weights=year_weights, k=num_accidents)

    for i in range(1, num_accidents + 1):
        an = ans[i - 1]
        num_acc_str = f"{an}0000{i:04d}"

        # 1. Caracteristiques
        mois = random.randint(1, 12)
        jour = random.randint(1, 28)
        hr = random.randint(0, 23)
        mn = random.randint(0, 59)

        if an in [2019, 2020]:
            hrmn = f"{hr:02d}{mn:02d}"
        elif an in [2021, 2022]:
            if random.random() < 0.3:
                hrmn = f"20{random.randint(10,23)}-08-{random.randint(10,28)}"
            else:
                hrmn = f"{hr:02d}:{mn:02d}"
        else:
            hrmn = f"{hr:02d}:{mn:02d}"

        lum = random.choices(
            [1, 2, 3, 4, 5], weights=[0.50, 0.10, 0.15, 0.05, 0.20], k=1
        )[0]

        is_dom = random.random() < 0.10
        if is_dom:
            dep = random.choice(dom_deps)
            lat = round(random.uniform(14.0, 17.0), 5)
            long = round(random.uniform(-62.0, -60.0), 5)
        else:
            dep = random.choice(metropole_deps)
            lat = round(random.uniform(42.0, 51.0), 5)
            long = round(random.uniform(-5.0, 10.0), 5)

        com = dep + f"{random.randint(1,999):03d}"
        agg = random.choices([1, 2], weights=[0.45, 0.55], k=1)[0]
        int_val = random.choices(
            range(1, 10),
            weights=[0.6, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05],
            k=1,
        )[0]
        atm = random.choices(
            range(1, 10),
            weights=[0.55, 0.1, 0.1, 0.05, 0.05, 0.05, 0.05, 0.025, 0.025],
            k=1,
        )[0]
        col = random.randint(1, 7)
        adr = random.choice(adresses)

        num_acc_val = num_acc_str
        acc_id_val = None
        if an in [2021, 2022] and random.random() < 0.2:
            acc_id_val = num_acc_str
            num_acc_val = None

        carac_data.append(
            {
                "Num_Acc": num_acc_val,
                "Accident_Id": acc_id_val,
                "jour": jour,
                "mois": mois,
                "an": an,
                "hrmn": hrmn,
                "lum": lum,
                "dep": dep,
                "com": com,
                "agg": agg,
                "int": int_val,
                "atm": atm,
                "col": col,
                "adr": adr,
                "lat": lat,
                "long": long,
            }
        )

        # 2. Lieux
        catr = random.choices(
            range(1, 8), weights=[0.1, 0.1, 0.35, 0.35, 0.05, 0.025, 0.025], k=1
        )[0]
        circ = random.choices([1, 2, 3, 4], weights=[0.2, 0.6, 0.1, 0.1], k=1)[0]
        nbv = random.choices(
            [1, 2, 3, 4, 5, 6], weights=[0.1, 0.5, 0.2, 0.1, 0.05, 0.05], k=1
        )[0]
        surf = random.choices(
            range(1, 10),
            weights=[0.5, 0.3, 0.05, 0.05, 0.02, 0.02, 0.02, 0.02, 0.02],
            k=1,
        )[0]
        situ = random.choices(
            range(1, 9), weights=[0.6, 0.1, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05], k=1
        )[0]

        lieu_row = {
            "Num_Acc": num_acc_str,
            "catr": catr,
            "voie": f"{random.randint(1, 100)}",
            "v1": random.randint(0, 2),
            "v2": random.choice(["", "A", "B"]),
            "circ": circ,
            "nbv": nbv,
            "vosp": random.randint(0, 3),
            "prof": random.randint(1, 4),
            "pr": random.randint(0, 50),
            "pr1": random.randint(0, 1000),
            "plan": random.randint(1, 4),
            "lartpc": random.randint(0, 50),
            "larrout": random.randint(50, 200),
            "surf": surf,
            "infra": random.randint(0, 7),
            "situ": situ,
            "env1": random.randint(0, 99),
        }
        if an >= 2023:
            lieu_row["vma"] = random.choice([30, 50, 70, 80, 90, 110, 130])
        lieux_data.append(lieu_row)

        # 3. Vehicules & Usagers
        num_vehicules = random.choices(
            [1, 2, 3, 4], weights=[0.20, 0.55, 0.20, 0.05], k=1
        )[0]

        for v_idx in range(num_vehicules):
            id_vehicule = v_idx + 1
            num_veh = ["A01", "B01", "C01", "D01"][v_idx]
            catv = random.choices(
                [7, 2, 30, 33, 1, 13], weights=[0.65, 0.10, 0.05, 0.05, 0.05, 0.10], k=1
            )[0]

            vehic_data.append(
                {
                    "Num_Acc": num_acc_str,
                    "id_vehicule": id_vehicule,
                    "num_veh": num_veh,
                    "senc": random.randint(0, 2),
                    "catv": catv,
                    "obs": random.randint(0, 16),
                    "obsm": random.randint(0, 9),
                    "choc": random.randint(0, 9),
                    "manv": random.randint(0, 26),
                    "motor": random.randint(1, 6),
                    "occutc": random.randint(0, 50) if catv in [37, 38, 39, 40] else 0,
                }
            )

            num_usagers = random.choices([1, 2, 3], weights=[0.60, 0.30, 0.10], k=1)[0]
            for u_idx in range(num_usagers):
                place = 1 if u_idx == 0 else random.randint(2, 9)
                catu = random.choices([1, 2, 3], weights=[0.65, 0.25, 0.10], k=1)[0]
                grav = random.choices(
                    [1, 2, 3, 4], weights=[0.55, 0.05, 0.15, 0.25], k=1
                )[0]
                sexe = random.choices([1, 2], weights=[0.60, 0.40], k=1)[0]

                # Age distribution (normal ~38 yo, sd=15)
                an_nais = int(np.clip(np.random.normal(1986, 15), 1930, 2010))
                secu1 = random.choices(
                    range(0, 10),
                    weights=[0.05, 0.8, 0.05, 0.02, 0.02, 0.02, 0.01, 0.01, 0.01, 0.01],
                    k=1,
                )[0]

                usag_data.append(
                    {
                        "Num_Acc": num_acc_str,
                        "id_vehicule": id_vehicule,
                        "num_veh": num_veh,
                        "place": place,
                        "catu": catu,
                        "grav": grav,
                        "sexe": sexe,
                        "an_nais": an_nais,
                        "trajet": random.randint(0, 9),
                        "secu1": secu1,
                        "secu2": -1,
                        "secu3": -1,
                        "locp": -1,
                        "actp": -1,
                        "etatp": -1,
                    }
                )

        if i % 50000 == 0:
            logging.info(f"Processed {i} accidents...")

    # 4. Export CSV
    logging.info("Saving CSVs...")
    pd.DataFrame(carac_data).to_csv(
        os.path.join(out_dir, "caracteristiques.csv"), index=False
    )
    pd.DataFrame(lieux_data).to_csv(os.path.join(out_dir, "lieux.csv"), index=False)
    pd.DataFrame(vehic_data).to_csv(os.path.join(out_dir, "vehicules.csv"), index=False)
    pd.DataFrame(usag_data).to_csv(os.path.join(out_dir, "usagers.csv"), index=False)

    # 5. Generate Shadow Log with Intentional Drift
    logging.info("Generating Shadow Log with Intentional Drift...")
    # Shadow log mimics harmonized usagers, let's take a sample of the generated usag_data
    shadow_sample = random.choices(usag_data, k=5000)
    shadow_df = pd.DataFrame(shadow_sample)
    # Appliquer un drift sur an_nais (vieillissement de 5 ans en moyenne)
    shadow_df["an_nais"] = shadow_df["an_nais"] - 5
    # Drift sur le trajet (shift de distribution)
    shadow_df["trajet"] = shadow_df["trajet"].apply(
        lambda x: 9 if random.random() < 0.3 else x
    )

    shadow_df.to_csv(os.path.join(prod_dir, "shadow_log.csv"), index=False)

    logging.info("Successfully generated:")
    logging.info(f" - {len(carac_data)} accidents in caracteristiques.csv")
    logging.info(f" - {len(lieux_data)} rows in lieux.csv")
    logging.info(f" - {len(vehic_data)} rows in vehicules.csv")
    logging.info(f" - {len(usag_data)} rows in usagers.csv")
    logging.info(f" - {len(shadow_df)} rows in shadow_log.csv")


if __name__ == "__main__":
    generate_synthetic_baac()
