#%%
from dash import html, Input, Output, State, ctx, dcc
import dash
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
import pandas as pd
import os
from flask import request
from datetime import datetime
from waitress import serve


def formatar_data(df):
    if 'data_nascimento' in df.columns:
        df['data_nascimento'] = pd.to_datetime(df['data_nascimento'], errors='coerce').dt.strftime('%d/%m/%Y')
    return df

try:
    df_second = formatar_data(pd.read_pickle('data/df_second.pkl')).sort_values('nome')
    df_second['id'] = df_second['id'].apply(lambda x: int(x.split('_')[1]))

except Exception as e:
    print(f"Error loading second data: {e}")
    df_second = pd.DataFrame(columns=['id', 'nome', 'nome_mae', 'data_nascimento', 'sexo', 'numero_cpf'])

try:
    df_first = formatar_data(pd.read_pickle('data/df_first.pkl')).sort_values('nome')
    df_first['id'] = df_first['id'].apply(lambda x: int(x.split('_')[1]))
except Exception as e:
    print(f"Error loading first data: {e}")
    df_first = pd.DataFrame(columns=['id', 'nome', 'nome_mae', 'data_nascimento', 'sexo', 'numero_cpf'])

try:
    df_third = formatar_data(pd.read_pickle('data/df_third.pkl')).sort_values('nome')
    df_third['id'] = df_third['id'].apply(lambda x: int(x.split('_')[1]))
except Exception as e:
    print(f"Error loading third data: {e}")
    df_third = pd.DataFrame(columns=['id', 'nome', 'nome_mae', 'data_nascimento', 'sexo', 'numero_cpf'])

try:
    df_principal = formatar_data(pd.read_pickle('data/df_no_cross.pkl'))
    if 'total_score' in df_principal.columns:
        df_principal['score_total'] = df_principal['total_score']
    df_principal = df_principal[df_principal['score_total'] >= 0.75]
except Exception as e:
    print(f"Error loading principal data: {e}")
    df_principal = pd.DataFrame(columns=['id_x', 'id_y', 'score_total'])
    df_principal['score_total'] = 0

df_first['Fonte'] = 'first'
df_second['Fonte'] = 'second'
df_third['Fonte'] = 'third'
#%%
df_second['numero_processo_second'] = df_second['numero_processo']
df_first['numero_processo_first'] = df_first['numero_processo']
#%%
#df_ids = df_principal['id_x'].tolist() + df_principal['id_y'].tolist()
# count = 0
# def take(df, tipo):
#     for i, row in df.iterrows():
#         global count
#         id_x = tipo + '_' + str(row['id'])
#         count += 1
#         print(count,'/',len(df))
#         df.loc[i, 'Encontrado'] = 'Sim' if id_x in df_ids else 'Nao'
#     count = 0
#     return df


# df_first = take(df_first, 'first')
# df_second = take(df_second, 'second')
# df_third = take(df_third, 'third')

# df_first.to_pickle('data/df_first.pkl')
# df_second.to_pickle('data/df_first.pkl')
# df_third.to_pickle('data/df_first.pkl')

df_principal['tipo_x'] = df_principal['id_x'].str.extract(r'(\w+)_')
df_principal['tipo_y'] = df_principal['id_y'].str.extract(r'(\w+)_')

map_dfs = {
    'first': df_first.set_index('id'),
    'second': df_second.set_index('id'),
    'third': df_third.set_index('id')
}

def style_css():
    return html.Link(rel='stylesheet', href='/assets/dbc.css')

defaultColDefMain = {
    "headerClass": 'center-aligned-header',
    "resizable": True,
    "sortable": True,
    "filter": True,
    "floatingFilter": True,
    "rowHeight": 28,
    "editable":True
}

defaultColDefRelated = {
    "headerClass": 'center-aligned-header',
    "resizable": True,
    "sortable": True,
    "rowHeight": 28,
    "editable":True
}

dashGridOptionsMain={
            "rowSelection": "single",
            "defaultColDef": defaultColDefMain,
        }
dashGridOptionsRelated={
            "rowSelection": "single",
            "defaultColDef": defaultColDefRelated,
        }

def generate_columns(df):
    cols = ['id','nome', 'nome_mae', 'data_nascimento', 'sexo', 'numero_cpf', 'Encontrado']
    cols = ['Encontrado', 'id', 'nome', 'nome_mae', 'data_nascimento', 'numero_cpf', 'sexo','numero_processo', 'descricao_regime_prisional']
    cols_list = [{"field": col, "headerName": col} for col in cols]

    # cols_list[0]={"field":"id", "headerName":"id", "floatingFilter":False}
    # cols_list[4]={"field":"sexo", "headerName":"sexo", "floatingFilter":False}

    return cols_list

def generate_related_columns(df):
    cols = ['id','nome', 'nome_mae', 'data_nascimento', 'sexo', 'score_total']
    cols = ['Fonte','id','numero_processo_second', 'numero_processo_first', 'nome', 'nome_mae', 'data_nascimento', 'numero_cpf', 'sexo', 'descricao_regime_prisional']
    return [{"field": col, "headerName": col} for col in cols]

dbc_css = style_css()
dash_extra_args = {}
if os.environ.get('APP_PATH', None) is not None:
    dash_extra_args['routes_pathname_prefix'] = os.environ.get('APP_PATH')

app = dash.Dash(__name__, external_stylesheets=[dbc_css, dbc.themes.DARKLY], **dash_extra_args)


def create_aggrid(id, df, related=False):
    return dag.AgGrid(
        id=id,
        rowData=None if related else df.to_dict("records"),
        columnDefs=generate_related_columns(df) if related else generate_columns(df),
        className="ag-theme-alpine",
        dashGridOptions= dashGridOptionsMain if not related else dashGridOptionsRelated
    )

def create_tab(label, id, df):
    return dbc.Tab(create_aggrid(id=id, df=df), label=label, tab_id=id)


def create_related_col(label, id, df):
    return dbc.Col([
        html.Div(html.H6(label), className="md-3", id=str(id)+'-div'),
        create_aggrid(id=id, df=df, related=True)
    ])

app.layout = dbc.Container([

    html.H4("🔍 SISTEMA DE BUSCA POR SIMILARIDADE", className="text-center"),
    dbc.Row([
        dbc.Col([],md=1),
        dbc.Col([
            dbc.Card([
                dbc.Tabs([
                    create_tab("first", "grid-first", df_first,),
                    create_tab("second", "grid-second", df_second,),
                    create_tab("third", "grid-third", df_third,),
                ], id="tabs-grids", active_tab="grid-first")
            ])
        ], md=10),
        dbc.Col([],md=1)
        # dbc.Col([
        #     html.A("Score mínimo:"),
        #     dcc.Slider(
        #         id='score-slider',
        #         min=0.7,
        #         max=1,
        #         step=0.01,
        #         value=0.7,
        #         marks={i / 10: str(i / 10) for i in range(0, 11)},
        #         tooltip={"placement": "bottom", "always_visible": True},
        #         vertical=True
        #     )
        # ], md=1, className='d-none'),
    ]),

    html.Br(),


        dbc.Row([
            dbc.Col([], md=1),
            create_related_col("Relacionamento:", "related-df", df_first),
            # create_related_col("second", "related-second", df_second),
            # create_related_col("third", "related-third", df_third),
            dbc.Col([], md=1),
        ])

], fluid=True, className="dbc dbc-ag-grid")


# @app.callback(
#     Output('related-first-div', 'className'),
#     Output('related-first', 'className'),
#     Output('related-second-div', 'className'),
#     Output('related-third-div', 'className'),
#     Input('grid-first', 'selectedRows'),
#     Input('grid-second', 'selectedRows'),
#     Input('grid-third', 'selectedRows')
# )
# def update_layout(rows_first, rows_second, rows_third):
    
#     if rows_first and len(rows_first) > 0:
#         return "d-none","d-none", "col-md-6", "col-md-6"
#     else:
#         return  "col-md-4","col-md-4", "col-md-4", "col-md-4",


@app.callback(
    Output("grid-first", "rowData"),
    Output("grid-second", "rowData"),
    Output("grid-third", "rowData"),
    Input("tabs-grids", "active_tab")
)
def refresh_grid_data(active_tab):
    return (
        df_first.to_dict("records") if active_tab == "grid-first" else dash.no_update,
        df_second.to_dict("records") if active_tab == "grid-second" else dash.no_update,
        df_third.to_dict("records") if active_tab == "grid-third" else dash.no_update,
    )

@app.callback(
    Output("related-df", "rowData"),
    # Output("related-second", "rowData"),
    # Output("related-third", "rowData"),
    Input("grid-first", "selectedRows"),
    Input("grid-second", "selectedRows"),
    Input("grid-third", "selectedRows"),
    # Input("score-slider", "value")
)
def update_related(first_sel, second_sel, third_sel):
    sel_id = None
    tipo_origem = None

    def get_selection_info(source_type, selection):
        if selection:
            return f"{source_type}_{selection[0]['id']}", source_type
        return None, None

    if ctx.triggered_id == "grid-first":
        sel_id, tipo_origem = get_selection_info('first', first_sel)
    elif ctx.triggered_id == "grid-second":
        sel_id, tipo_origem = get_selection_info('second', second_sel)
    elif ctx.triggered_id == "grid-third":
        sel_id, tipo_origem = get_selection_info('third', third_sel)
    elif ctx.triggered_id == "score-slider":
        for source_type, selection in [('first', first_sel), ('second', second_sel), ('third', third_sel)]:
            sel_id, tipo_origem = get_selection_info(source_type, selection)
            if sel_id:
                break

    if not sel_id:
        return [], [], []
    
    score_threshold = 0.75
    filtered = df_principal[
        ((df_principal['id_x'] == sel_id) | (df_principal['id_y'] == sel_id)) &
        (df_principal['score_total'] >= score_threshold)
    ]

    results = {'first': [], 'second': [], 'third': []}

    for _, row in filtered.iterrows():
        if row['id_x'] == sel_id:
            tipo_alvo = row['tipo_y']
            id_alvo = row['id_y'].split('_')[1]
            score = row['score_total']
        else:
            tipo_alvo = row['tipo_x']
            id_alvo = row['id_x'].split('_')[1]
            score = row['score_total']

        if id_alvo.isdigit() and tipo_alvo in map_dfs:
            try:
                dados = map_dfs[tipo_alvo].loc[int(id_alvo)].to_dict()
                dados['score_total'] = round(score, 4)
                dados['id'] = id_alvo
                results[tipo_alvo].append(dados)
            except KeyError:
                continue


    df_first = pd.DataFrame.from_dict(results['first'])
    df_second = pd.DataFrame.from_dict(results['second'])
    df_third = pd.DataFrame.from_dict(results['third'])

    df_full = pd.concat([df_first, df_second, df_third])
    # df_full[['Fonte','id','numero_processo', 'nome', 'nome_mae', 'data_nascimento', 'numero_cpf', 'sexo', 'descricao_regime_prisional', 'Encontrado']] = ''
    # df_full = df_full[]['Fonte','id','numero_processo', 'nome', 'nome_mae', 'data_nascimento', 'numero_cpf', 'sexo', 'descricao_regime_prisional', 'Encontrado']
    full_dict = df_full.to_dict('records')

    # print(df_full)

    # return full_dict, results['second'], results['third']
    return full_dict


server = app.server

@server.before_request
def log_request_info():
    print(f"IP do Host: {request.remote_addr} " + datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

def run_server():
    serve(app=server, host='0.0.0.0', port=8050, threads=16)
