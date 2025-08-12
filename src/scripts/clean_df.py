import pandas as pd
from scripts.db_dump import df_1, df_2, df_3




def preprocess_data(df, suffix):
    df_columns = df.columns.tolist()
    text_cols = [i + suffix for i in df_columns]
    df.rename(columns=dict(zip(df_columns, text_cols)), inplace=True)
    print(df.columns)
    print(text_cols)
    for col in text_cols:
        if df[col].dtype == 'object':
            df[col] = df[col].str.upper().str.strip().str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')
            df[col] = df[col].apply(clean_df)
    return df

def clean_df(value):
    try:

        if value is None:
            return None

        value = str(value)
        value = value.upper()
        value = str(value).replace('  ', ' ')
        value = str(value).replace("\'", '')
        value = str(value).replace('Á', 'A')
        value = str(value).replace('É', 'E')
        value = str(value).replace('Í', 'I')
        value = str(value).replace('Ó', 'O')
        value = str(value).replace('Ú', 'U')
        value = str(value).replace('Ô', 'O')
        value = str(value).replace('Ç', 'C')
        value = str(value).replace('Ã', 'A')
        value = str(value).replace('Â', 'A')

        if value.startswith(' '):
            value = value[1:]
        if value.endswith(' '):
            value = value[:-1]

    except Exception as e:
        print(e)
        return None
    return value



def main():
    df_1 = preprocess_data(df_1, '')
    df_2  = preprocess_data(df_2, '')
    df_3 = preprocess_data(df_3, '')

    df_1.to_pickle('data/df_first.pkl')
    df_2.to_pickle('data/df_second.pkl')
    df_3.to_pickle('data/df_third.pkl')