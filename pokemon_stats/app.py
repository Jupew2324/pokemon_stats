from flask import Flask, render_template, request
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

app = Flask(__name__)

# Carregar o arquivo de dados
data_file = 'static/data/All_Pokemon.csv'
data = pd.read_csv(data_file)

# Lista de nomes de Pokémon
pokemon_names = data['Name'].tolist()
# Colunas para matchups de tipo
against_columns = [col for col in data.columns if col.startswith('Against')]

def create_matchup_heatmap(pokemon_row):
    """Gerar gráfico de barras empilhadas como mapa de calor para um único Pokémon."""
    matchups = pokemon_row[against_columns].values
    types = [col.replace('Against ', '') for col in against_columns]

    fig = go.Figure(data=[
        go.Bar(
            x=types,
            y=matchups,
            marker=dict(color=matchups, colorscale='Viridis'),
            text=[f"{v:.2f}" for v in matchups],
            textposition='auto',
            name=pokemon_row['Name']
        )
    ])

    fig.update_layout(
        title=f"Fraquezas de {pokemon_row['Name']} (Mapa de Calor)",
        xaxis_title="Tipos",
        yaxis_title="Multiplicador de Dano",
        template="plotly_white"
    )

    return fig.to_html(full_html=False)

@app.route('/')
def index():
    return render_template('index.html', pokemons=pokemon_names)

@app.route('/analyze', methods=['POST'])
def analyze():
    # Obter os Pokémons selecionados
    selected_pokemon = [
        request.form.get('pokemon-1'),
        request.form.get('pokemon-2'),
        request.form.get('pokemon-3'),
        request.form.get('pokemon-4'),
        request.form.get('pokemon-5'),
        request.form.get('pokemon-6')
    ]

    if None in selected_pokemon or len(set(selected_pokemon)) < 6:
        return "Por favor, selecione exatamente 6 Pokémons diferentes.", 400

    # Filtrar dados para os Pokémon selecionados
    filtered_data = data[data['Name'].isin(selected_pokemon)]

    # Gerar gráficos de matchup para cada Pokémon
    matchup_graphs = {
        row['Name']: create_matchup_heatmap(row)
        for _, row in filtered_data.iterrows()
    }

    # Radar chart (Comparativo de Estatísticas)
    radar_categories = ['HP', 'Att', 'Def', 'Spe', 'Spa', 'Spd']
    radar_fig = go.Figure()
    for _, row in filtered_data.iterrows():
        radar_fig.add_trace(go.Scatterpolar(
            r=row[radar_categories].values,
            theta=radar_categories,
            fill='toself',
            name=row['Name']
        ))
    radar_fig.update_layout(
        polar=dict(radialaxis=dict(visible=True)),
        title="Comparativo de Estatísticas (Radar)",
        showlegend=True
    )
    radar_html = radar_fig.to_html(full_html=False)

    # Bar chart (Estatísticas Empilhadas)
    bar_fig = go.Figure()
    for _, row in filtered_data.iterrows():
        bar_fig.add_trace(go.Bar(
            x=radar_categories,
            y=row[radar_categories].values,
            name=row['Name']
        ))
    bar_fig.update_layout(
        barmode='stack',
        title="Estatísticas Empilhadas por Pokémon",
        xaxis_title="Atributos",
        yaxis_title="Valores",
        showlegend=True
    )
    bar_html = bar_fig.to_html(full_html=False)

    # Gráfico de radar para médias
    mean_stats = filtered_data[radar_categories].mean()
    mean_radar_fig = go.Figure()
    mean_radar_fig.add_trace(go.Scatterpolar(
        r=mean_stats.values,
        theta=radar_categories,
        fill='toself',
        name='Média'
    ))
    mean_radar_fig.update_layout(
        polar=dict(radialaxis=dict(visible=True)),
        title="Estatísticas Médias dos Pokémon Selecionados (Radar)",
        showlegend=True
    )
    mean_radar_html = mean_radar_fig.to_html(full_html=False)

    # Histograma para os Pokémons Selecionados
    hist_fig = go.Figure()
    for atributo in radar_categories:
        hist_fig.add_trace(go.Histogram(
            x=filtered_data[atributo],
            name=atributo,
            opacity=0.75
        ))
    hist_fig.update_layout(
        title="Distribuição de Atributos dos Pokémon Selecionados",
        xaxis_title="Valor do Atributo",
        yaxis_title="Frequência",
        barmode='overlay',
        showlegend=True
    )
    hist_html = hist_fig.to_html(full_html=False)

    return render_template(
        'index.html',
        pokemons=pokemon_names,
        radar_graph=radar_html,
        bar_graph=bar_html,
        mean_radar_graph=mean_radar_html,
        hist_graph=hist_html,  # Passa o histograma para o template
        matchup_graphs=matchup_graphs  # Passa o mapa de calor para o template
    )

@app.route('/exploratory')
def exploratory_analysis():
    exploratory_data = pd.read_csv(data_file)
    atributos = ['HP', 'Att', 'Def', 'Spa', 'Spd', 'Spe']

    fig = make_subplots(rows=2, cols=3, subplot_titles=atributos)

    for i, atributo in enumerate(atributos):
        row = i // 3 + 1
        col = i % 3 + 1
        fig.add_trace(go.Histogram(
            x=exploratory_data[atributo],
            nbinsx=20,
            marker_color='blue',
            opacity=0.7,
            name=atributo
        ), row=row, col=col)

    fig.update_layout(
        title="Distribuição dos Atributos dos Pokémon",
        showlegend=False,
        height=600,
        template="plotly_white"
    )

    exploratory_html = fig.to_html(full_html=False)

    return render_template('exploratory.html', graphs=[exploratory_html])

if __name__ == '__main__':
    app.run(debug=True)
