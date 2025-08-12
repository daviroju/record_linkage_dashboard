#%%
import pandas as pd
import recordlinkage
from recordlinkage.index import SortedNeighbourhood
from numpy import nan
from scripts.cleaned_df import main
import time
#%%
now = int(time.time())
try:
    main()
except Exception as e:
    print(e)
    print('Erro ao extrair os dados do banco de dados.')
############################# SETTINGS ###################################
WINDOW = 13
JOBS = -1
THRESHOLD = 0.75
##########################################################################
df_projudi = pd.read_pickle('data/df_projudi.pkl')
df_bnmp = pd.read_pickle('data/df_bnmp.pkl')
df_goiaspen = pd.read_pickle('data/df_goiaspen.pkl')

df_projudi.loc[:, 'id'] = 'projudi_' + df_projudi['id'].astype(str)
df_bnmp.loc[:, 'id'] = 'bnmp_' + df_bnmp['id'].astype(str)
df_goiaspen.loc[:, 'id'] = 'goiaspen_' + df_goiaspen['id'].astype(str)
#%%
# df_ = pd.read_pickle('data/df_no_cross.pkl')
# df_ = df_[df_['total_score']>=0.80]
# df__ = df_['id_y'].apply(lambda x: x if x.split('_')[1] == '1713526' else nan)
# df_ = df_[df_['id_y'].str.contains('1713526')]

#%%
def preprocess(df):
    df = df.copy()
    df['data_nascimento'] = pd.to_datetime(df['data_nascimento'], dayfirst=True).dt.strftime('%Y%m%d')
    return df

df1_clean = preprocess(df_projudi)
df2_clean = preprocess(df_bnmp)
df3_clean = preprocess(df_goiaspen)

#%%
def create_final_result(df1, df2, matches):
    df1_reset = df1.reset_index()
    df2_reset = df2.reset_index()

    df1_reset['index_1'] = df1.index
    df2_reset['index_2'] = df2.index

    matches = matches.reset_index()

    final_df = matches.merge(
        df1_reset,
        left_on='level_0',
        right_on='index_1',
        how='left'
    ).merge(
        df2_reset,
        left_on='level_1',
        right_on='index_2',
        how='left'
    )
    final_df = final_df.sort_values(by=['total_score', 'nome_score', 'mae_score'], ascending=False)
    return final_df

df_full = pd.concat([df1_clean, df2_clean, df3_clean]).reset_index(drop=True)

indexer = recordlinkage.Index()
indexer.add(SortedNeighbourhood('data_nascimento', window=WINDOW))
indexer.block(left_on='nome', right_on='nome')

candidate_pairs = indexer.index(df_full)

compare = recordlinkage.Compare(n_jobs=JOBS)
compare.string('nome', 'nome', method='levenshtein', label='nome_score')
compare.string('nome_mae', 'nome_mae', method='levenshtein', label='mae_score')
compare.string('data_nascimento', 'data_nascimento', label='nascimento_score')

features = compare.compute(candidate_pairs, df_full)


features['total_score'] = (0.5 * features['nome_score'] +
                          0.3 * features['mae_score'] +
                          0.2 * features['nascimento_score'])

matches = features[features['total_score'] >= THRESHOLD]
df_matches = create_final_result(df_full, df_full, matches)
df_matches_cleaned = df_matches[['id_x', 'id_y', 'total_score', 'nome_score','mae_score','nascimento_score', 'nome_x', 'nome_y',
                                'nome_mae_x', 'nome_mae_y',
                                'data_nascimento_x', 'data_nascimento_y']]


df_matches_all = df_matches_cleaned[df_matches_cleaned['id_x'] != df_matches_cleaned['id_y']].sort_values(by=['nome_x'], ascending=True).reset_index(drop=True)
df = df_matches_all.copy()
df.to_pickle('data/df_no_cross.pkl')

print(f"Total de matches encontrados: {len(df_matches_cleaned)}")
now_ = int(time.time() - now)
print('Tempo gasto:', now_)
print('WINDOW:',WINDOW)
print('JOBS:',JOBS)
print('Tarefa finalizada.')


count = 0
def take(df, tipo):
    for i, row in df.iterrows():
        global count
        id_x = str(row['id'])
        count += 1
        print(count,'/',len(df), '/', id_x)
        df.loc[i, 'Encontrado'] = 'Sim' if id_x in df_ids else 'Nao'
        
    count = 0
    return df


df['score_total'] = df['total_score']
df = df[df['score_total'] >= THRESHOLD]

df_ids = df['id_x'].tolist() + df['id_y'].tolist()
df_bnmp = take(df_bnmp, 'bnmp')
df_projudi = take(df_projudi, 'projudi')
df_goiaspen = take(df_goiaspen, 'goiaspen')

df_bnmp.to_pickle('data/df_bnmp.pkl')
df_projudi.to_pickle('data/df_projudi.pkl')
df_goiaspen.to_pickle('data/df_goiaspen.pkl')

# N = 5000
# df['cross_doble'] = False
#
# for i in range(1, N + 1):
#     df['cross_doble'] |= (df['id_x'] == df['id_y'].shift(-i))
#     df['cross_doble'] |= (df['id_x'] == df['id_y'].shift(i))
#
# df_no_cross = df[df['cross_doble']!=True]
# df_no_cross.to_pickle('df_no_cross.pkl')

# %%