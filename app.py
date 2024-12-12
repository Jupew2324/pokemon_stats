from flask import Flask, render_template, request
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Inicializar o aplicativo Flask
app = Flask(__name__)

# Carregar o arquivo de dados
data_file = 'static/data/All_Pokemon.csv'
data = pd.read_csv(data_file)

# Lista de nomes de Pokémon
pokemon_names = data['Name'].tolist()

# Atributos de estatísticas
stats_columns = ['HP', 'Att', 'Def', 'Spa', 'Spd', 'Spe']

# Colunas para matchups de tipo
against_columns = [col for col in data.columns if col.startswith('Against')]

def create_combined_matchup_heatmap(pokemon_rows):
    """Gerar um heatmap para vários Pokémon baseado em suas fraquezas, exibindo uma grade de Pokémon vs Tipos."""
    matchups = pokemon_rows[against_columns].values
    types = [col.replace('Against ', '') for col in against_columns]
    pokemon_names = pokemon_rows['Name'].tolist()

    fig = go.Figure(data=go.Heatmap(
        z=matchups,
        x=types,
        y=pokemon_names,
        colorscale='viridis',  # Escala de cores válida
        showscale=True,
        zmin=0,
        zmax=4
    ))

    fig.update_layout(
        title="Fraquezas dos Pokémon Selecionados (Heatmap)",
        xaxis_title="Tipos de Pokémon",
        yaxis_title="Pokémon",
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
        request.form.get(f'pokemon-{i}') for i in range(1, 7)
    ]

    if None in selected_pokemon or len(set(selected_pokemon)) < 6:
        return "Por favor, selecione exatamente 6 Pokémons diferentes.", 400

    # Filtrar dados para os Pokémon selecionados
    filtered_data = data[data['Name'].isin(selected_pokemon)]

    # Gerar gráficos
    matchup_html = create_combined_matchup_heatmap(filtered_data)

    radar_categories = ['HP', 'Att', 'Def', 'Spa', 'Spd', 'Spe']
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

    # Gráfico radar de médias
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

    # Histograma de atributos
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

    # Gerar gráficos de barras individuais
    bar_charts_html = []
    colors = ['#FF5733', '#33FF57', '#3357FF', '#FF33A6', '#FFC300', '#C700FF']  # Cores distintas para os atributos

    for _, row in filtered_data.iterrows():
        # Criar uma nova figura para cada Pokémon
        bar_fig = go.Figure()

        # Adicionar a barra para cada atributo com uma cor diferente
        for i, attribute in enumerate(radar_categories):
            bar_fig.add_trace(go.Bar(
                x=[attribute],  # Usar apenas o nome do atributo como eixo X
                y=[row[attribute]],  # Valor do atributo
                name=attribute,  # Nome do atributo
                marker_color=colors[i]  # Cor correspondente ao atributo
            ))

        # Atualizar o layout do gráfico
        bar_fig.update_layout(
            title=f"Estatísticas de {row['Name']}",
            xaxis_title="Atributos",
            yaxis_title="Valores",
            template="plotly_white",
            showlegend=False  # Opcional: mostrar ou ocultar a legenda
        )

        # Adicionar o gráfico à lista de gráficos HTML
        bar_charts_html.append(bar_fig.to_html(full_html=False))

    # Renderizar o template com todos os gráficos
    return render_template(
        'index.html',
        pokemons=pokemon_names,
        radar_graph=radar_html,
        bar_graph=bar_html,
        mean_radar_graph=mean_radar_html,
        hist_graph=hist_html,
        matchup_graph=matchup_html,
        individual_bar_graphs=bar_charts_html  # Adicionando os gráficos individuais
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
