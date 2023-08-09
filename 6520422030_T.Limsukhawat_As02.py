# Assignment 2 (Starbucks)
## Import Library
import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import requests

## Read file
df = pd.read_csv('/Users/thanyalak/Desktop/5001/Starbucks.csv')
t1 = df.copy()
t1['city_new'].fillna(t1['City'], inplace=True)
t1['province_new'].fillna(t1['State/Province'], inplace=True)

## ------------------------------------------------------------------------------------ ##

### Question 1 (First Diagrm)
plot1_df = t1[['Country', 'Store Number']][t1['Country'].isin(['TH', 'MY', 'VN'])]

country_full_name = {'TH': 'Thailand', 'MY': 'Malaysia', 'VN': 'Vietnam'}
plot1_df['Country'] = plot1_df['Country'].replace(country_full_name)

plot1_df = plot1_df['Country'].value_counts().reset_index().rename(columns = {'Number of Store' : 'Country', 'count' : 'Number of Store'})
print(plot1_df)

# Create Dash app
app = dash.Dash(__name__)

# Define custom colors for each country
custom_colors = {
    'Thailand': 'lightblue',
    'Vietnam': 'lightgreen',
    'Malaysia': 'salmon'
}

# Create the Plotly figure
single_chart = px.bar(
    plot1_df,
    x='Country',
    y='Number of Store',
    hover_name='Number of Store',
    title='Number of Starbucks stores among Thailand, Vietnam, and Malaysia',
    template='plotly_dark',
    color=[custom_colors[country] for country in plot1_df['Country']]
)

single_chart.update_traces(showlegend=False)

# Define the layout of the app
app.layout = html.Div([
    dcc.Graph(id='single-chart',
              figure=single_chart,
              config={'displayModeBar': False})
])

if __name__ == '__main__':
    app.run_server(port=8051, debug=True)

## ------------------------------------------------------------------------------------ ##

### Question 2 (Two Components)
plot2_df = t1[['Country', 'city_new', 'Store Number']][t1['Country'].isin(['TH', 'MY', 'VN'])]
country_full_name = {'TH': 'Thailand', 'MY': 'Malaysia', 'VN': 'Vietnam'}
plot2_df['Country'] = plot2_df['Country'].replace(country_full_name)
plot2_df = plot2_df[['Country', 'city_new']].value_counts().reset_index().rename(columns={'city_new' : 'City','count': 'Num_Store'}).sort_values(by='Num_Store', ascending=False)
plot2_pivot = plot2_df.pivot_table(index=['Country', 'City'], values='Num_Store', aggfunc='sum').reset_index()
country_counts = plot2_pivot.groupby('Country')['Num_Store'].sum().reset_index()
country_counts = country_counts.sort_values(by='Num_Store', ascending=False)
total_num_stores = plot2_df['Num_Store'].sum()

# Create Dash app
app = dash.Dash(__name__)

# Create the Dash DataTable
table = dash_table.DataTable(
    id='datatable',
    columns=[{'name': col, 'id': col} for col in plot2_pivot.columns],
    data=plot2_pivot.to_dict('records'),
)

# Create dropdown list options
dropdown_options = [{'label': 'All Countries', 'value': 'All Countries'}] + [{'label': country, 'value': country} for country in country_counts['Country']]

# Create the dropdown component
dropdown = dcc.Dropdown(
    id='country-dropdown',
    options=dropdown_options,
    value=None,
    placeholder="Select a country"
)

# Create the scorecard component
scorecard = html.Div(id='scorecard', style={'font-size': '24px'})

# Create the treemap component
treemap = dcc.Graph(id='treemap')

# Define the layout of the app
app.layout = html.Div([
    html.Div([
        html.Div([
            dropdown,
            html.Br(),
            html.Div(html.H1(id='table-title'), style={'text-align':'center'}),
            treemap,
        ], style={'flex': '50%'}),
        html.Div([
            html.Div(html.B(scorecard), style={'text-align': 'center', 'margin-top': '20px'}),
            html.Br(),
            html.Div(table, style={'margin-left' : '50px', 'height': '1200px', 'width' : '600px', 'overflow-y' : 'scroll'}),
        ], style={'flex': '50%'}),
    ], style={'display': 'flex'}),
], style={'display': 'flex', 'height':'100vh'})


# Callbacks
@app.callback(
    [Output('datatable', 'data'), Output('scorecard', 'children'), Output('table-title', 'children')],
    [Input('country-dropdown', 'value')]
)
def update_diagram(selected_country):
    if selected_country is None or selected_country == 'All Countries':
        scorecard_text = f"All Countries: {total_num_stores} stores"
        combined_data = plot2_pivot.copy()
        title = "Starbucks Store Counts for All Countries"
        return combined_data.to_dict('records'), scorecard_text, title
    else:
        filtered_data = plot2_pivot[plot2_pivot['Country'] == selected_country]
        num_stores = country_counts.loc[country_counts['Country'] == selected_country, 'Num_Store'].values[0]
        scorecard_text = f"{selected_country}: {num_stores} stores"
        title = f"Starbucks Store Counts for {selected_country}"
        return filtered_data.to_dict('records'), scorecard_text, title

@app.callback(
    Output('treemap', 'figure'),
    [Input('country-dropdown', 'value')]
)
def update_treemap(selected_country):
    if selected_country is None or selected_country == 'All Countries':
        treemap_data = country_counts
    else:
        treemap_data = plot2_pivot[plot2_pivot['Country'] == selected_country]
    
    fig = px.treemap(plot2_df, path=['Country', 'City'], values='Num_Store',
                     color_discrete_sequence=px.colors.qualitative.Pastel1)
    
    # Customize the treemap layout for portrait orientation
    fig.update_layout(
        autosize=True,
        width=700,
        height=1100,
        margin=dict(l=0, r=0, b=0, t=0)
    )
    
    return fig

if __name__ == '__main__':
    app.run_server(port = 8052, debug=True)

## ------------------------------------------------------------------------------------ ##

### Question 3 (Map Chart)
# Filter Data
big_city = ['Chiang Mai', 'Phuket', 'Bangkok']
plot3_df = t1[(t1['Country'] == 'TH') & (t1['province_new'].isin(big_city))]
plot3_df['province_new'] = plot3_df['province_new'].replace('Bangkok', 'Bangkok Metropolis')
plot3_df = plot3_df.groupby('province_new')['Store Number'].count().to_frame().reset_index().sort_values(by = 'Store Number', ascending = False).rename(columns={'province_new':'Province', 'Store Number':'Num_Store'})

# Load GeoJSON data for Thailand provinces
geojson_response = requests.get('https://raw.githubusercontent.com/apisit/thailand.json/master/thailand.json')
geojson_file = geojson_response.json()

# Create the filled Thailand map with heat color levels
fig = px.choropleth_mapbox(
    plot3_df,
    geojson=geojson_file,
    locations='Province',
    featureidkey='properties.name',
    color='Num_Store',
    color_continuous_scale='Aggrnyl_r',
    mapbox_style='carto-positron',  # Choose mapbox style
    zoom=5,
    center={"lat": 13.7563, "lon": 100.5018}, 
    opacity=0.7,
    labels={'Num_Store': 'Number of Stores'},
    title='Number of Starbucks Store in Chiang Mai, Phuket, and Bangkok',
)

fig.update_geos(
    showcoastlines=True,
    coastlinecolor='Black',
    showland=True,
    landcolor='white',
)

# Create the Dash app
app = dash.Dash(__name__)

# Define the layout of the app
app.layout = html.Div([
    dcc.Graph(id="filled-thailand-map", figure=fig, style={'width':'100%', 'height':'1000px'}), 
])

# Run the app
if __name__ == "__main__":
    app.run_server(port=8054, debug=True)

## ------------------------------------------------------------------------------------ ##