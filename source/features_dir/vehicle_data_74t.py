
def load_df_vehicle_data():
    import pandas as pd
    from source.config import INTERIM_DATA_DIR, EXTERNAL_DATA_DIR

    df_74t_vehicle_weight_interim = pd.read_csv(INTERIM_DATA_DIR / "vehicle weight from 74t.csv")
    df_vehicle_matching = pd.read_csv(EXTERNAL_DATA_DIR / "bil_tilhenger_matching.csv")

    # Holds valid weight registrations for both truck and trailer
    df_74t_vehicle_weight = pd.concat(
        [
            df_74t_vehicle_weight_interim.merge(
                df_vehicle_matching[[col, 'ekvipasje']], 
                left_on='VIN', right_on=col, 
                how='inner'
            )
            for col in ['VIN_lastebil', 'VIN_tilhenger']
        ]
    ).drop(columns=['VIN_lastebil', 'VIN_tilhenger'], errors='ignore').dropna()

    return df_74t_vehicle_weight
