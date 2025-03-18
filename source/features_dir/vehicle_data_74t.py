
def df_truck_vehicle_data():
    '''
    Laster opp df med all kjøretøysdata logget på lastebiler fra 2021-2024.
    Inkluderer kolonnen "ekvipasje".
    '''

    from source.config import EXTERNAL_DATA_DIR, INTERIM_DATA_DIR
    import pandas as pd

    df_ekvipasje = pd.read_csv(EXTERNAL_DATA_DIR / 'bil_tilhenger_matching.csv').drop_duplicates(subset='VIN_lastebil')
    df_vehicle_data = pd.read_csv(INTERIM_DATA_DIR / "vehicle weight from 74t.csv")
    df_trucks = df_ekvipasje['VIN_lastebil'].unique()

    df_vehicle_data = (
        df_vehicle_data[df_vehicle_data['VIN'].isin(df_ekvipasje['VIN_lastebil'])]
        .assign(
            år=pd.to_datetime(df_vehicle_data['Dato'], format='ISO8601').dt.year,
            ekvipasje=df_vehicle_data['VIN'].map(df_ekvipasje.set_index('VIN_lastebil')['ekvipasje'])
        )
    )

    df = df_vehicle_data.copy()
    df["Snittforbruk kjøring (l/mil)"] = pd.to_numeric(df["Snittforbruk kjøring (l/mil)"].astype(str).str.replace(",", "."), errors="coerce")
    df["Liter kjøring"] = pd.to_numeric(df["Liter kjøring"].astype(str).str.replace(",", "."), errors="coerce")
    df["Distanse (km)"] = pd.to_numeric(df["Distanse (km)"].astype(str).str.replace(",", "."), errors="coerce")
    df["CO₂ (tonn)"] = pd.to_numeric(df["CO₂ (tonn)"].astype(str).str.replace(",", "."), errors="coerce")
    df["CO₂ snitt (kg/km)"] = pd.to_numeric(df["CO₂ snitt (kg/km)"].astype(str).str.replace(",", "."), errors="coerce")
    df["Snittvekt"] = pd.to_numeric(df["Snittvekt"].astype(str).str.replace(",", "."), errors="coerce")
    df = df.dropna(subset=["Snittforbruk kjøring (l/mil)", "Liter kjøring", "Distanse (km)", "CO₂ (tonn)", "Snittvekt", "CO₂ snitt (kg/km)"])

    return df


def df_truck_vechicle_data_groupby(groupby):
    '''
    laster opp kjøretøysdata, filtrerer på lastebiler, grupperer på ekvipasje og år, og aggregerer over ulike typer forbruk.

    Parameters:
        groupby [str]: array av kolonnenavn som skal groupby'es over.
    '''

    df = df_truck_vehicle_data()

    df['mil'] = df['Distanse (km)'] / 10

    df_agg = df.groupby(groupby).agg(
        liter_kjoring=('Liter kjøring', 'sum'),
        mil=('mil', 'sum')
    ).reset_index()

    df_agg['forbruk'] = df_agg['liter_kjoring'] / df_agg['mil']

    return df_agg

def convoy_vin():
    '''map fra str ekvipajse til arr av VIN'''
    from source.config import EXTERNAL_DATA_DIR
    import pandas as pd
    import itertools

    df = pd.read_csv(EXTERNAL_DATA_DIR / 'bil_tilhenger_matching.csv')
    return df.groupby('ekvipasje')[['VIN_lastebil']].apply(
        lambda x: set((itertools.chain.from_iterable(x.values)))
    ).to_dict()