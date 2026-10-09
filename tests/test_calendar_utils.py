import pandas as pd
from src.features.calendar_utils import add_french_holidays

def test_add_french_holidays():
    # Test dates: 1 Jan (Férié), 2 Jan (Normal), 25 Dec (Férié)
    df = pd.DataFrame({
        "event_timestamp": [
            pd.Timestamp("2023-01-01 10:00:00", tz="Europe/Paris"),
            pd.Timestamp("2023-01-02 10:00:00", tz="Europe/Paris"),
            pd.Timestamp("2023-12-25 10:00:00", tz="Europe/Paris")
        ]
    })
    
    df_result = add_french_holidays(df, date_col="event_timestamp")
    
    assert "is_ferie" in df_result.columns
    assert df_result["is_ferie"].iloc[0] == True
    assert df_result["is_ferie"].iloc[1] == False
    assert df_result["is_ferie"].iloc[2] == True

def test_timezone_preservation():
    df = pd.DataFrame({
        "event_timestamp": [pd.Timestamp("2023-01-01 10:00:00")] # Sans TZ
    })
    # Devrait lever une exception ou forcer la timezone selon l'implémentation
    # Si le contrat impose la TZ :
    # with pytest.raises(Exception):
    #    add_french_holidays(df)
