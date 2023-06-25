# -*- coding: utf-8 -*-
"""
Created on Sun Jun 25 12:59:16 2023

@author: samue
"""

import pandas as pd
import plotly.express as px
import streamlit as st
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import folium
import openrouteservice
from streamlit_folium import st_folium
import networkx as nx



def obtener_coordenadas_direccion(direccion):
    geolocator = Nominatim(user_agent="my_app")
    location = geolocator.geocode(direccion)


    if location is not None:
        latitud = location.latitude
        longitud = location.longitude
        return latitud, longitud
    else:
        return None
    
def distancia_entre ( client, or_long, or_lat, dst_long, dst_lat):
    locat_rev = [[or_lat, or_long]]
    locat_rev.append([dst_lat, dst_long])
    
    dm = openrouteservice.distance_matrix.distance_matrix(client, locat_rev, 'foot-walking', [0], [1],
                                                      metrics=['distance', 'duration'])
    
    return dm['distances'][0][0]


def create_map(center, zoom=14):
    m = folium.Map(location=list(reversed(center)), zoom_start=zoom)
    return m


def add_marker(m, coords, text="", color="red", icon="info-sign"):
    folium.map.Marker(list(reversed(coords)),
                      icon=folium.Icon(color=color,
                                       icon=icon
                                       ),
                      popup=text,
                      ).add_to(m)
    return m

# Cargar datos
datos = pd.read_csv('fgv-estacions-estaciones.csv', delimiter=';')
datos = datos.drop(['gid','Códi / Código','Pròximes Arribades / Próximas Llegadas','proximes_llegadas','geo_shape','Tipus / Tipo'], axis=1)
latitud, longitud = [], []
for index, row in datos.iterrows():
    geo = row['geo_point_2d']
    a = geo.split(',')
    latitud.append(a[0])
    longitud.append(a[1])
datos = datos.drop('geo_point_2d', axis=1)
datos['Latitud'] = latitud
datos['Longitud'] = longitud

# Obtener lista de nombres
nombres = datos['Nom / Nombre'].tolist()
nombres.sort()

# TÍTULO
st.title(":station: FGV Stations")
st.markdown("##")

# Texto indicativo y selección del usuario
col1, col2 = st.columns([1, 1])
with col2:
    
    mlines = ["ALL"]
    mlines.extend([x for x in range(1,11)])
    option = st.selectbox('Filter by line:',tuple(mlines))
    
    # Filtrar datos según la selección

# Mostrar datos filtrados
with col1:
    title = st.text_input('Write your location:', "Conde de Altea 39, Valencia, España")
    

    
###### OBTENER COORDENADAS DE LOCATION
 
col1, col2 = st.columns([1, 1])
coordenadas = obtener_coordenadas_direccion(title)
if coordenadas:
        
        ###### SACAR LAS DISTANCIAS A CADA PARADA
    
    datos["Distancia (km)"] = datos['Nom / Nombre']
    for i in range(len(datos['Nom / Nombre'])):
        coordenadas2 = [datos["Latitud"][i], datos["Longitud"][i]]
        d = geodesic(coordenadas, coordenadas2).kilometers
        datos["Distancia (km)"][i] = d
    
    if option != "ALL":
        lista = []
        for index,row in datos.iterrows():
            print(row["Línia / Línea"])
            if str(option) in row["Línia / Línea"].split(","):
                lista.append(tuple(row))    
        df = pd.DataFrame(lista, columns = list(datos.columns))
        df = df.sort_values("Distancia (km)")
    
    else:
        df = datos
        df = df.sort_values("Distancia (km)")
    df["ID"] = [x for x in range(len(df["Longitud"]))]
    with col1:
        st.write("The five nearest stations:")
        st.write(df[['Nom / Nombre', 'Línia / Línea', 'Distancia (km)']].head())
    
    coordenadas = [x for x in reversed(coordenadas)]
    m = create_map(coordenadas,zoom=13)
    m = add_marker(m, coordenadas, color="white", text="Your Location")
    df["marker"] = df["Nom / Nombre"]
    dic_colores = {}
    colores = ["beige","pink","red","cadetblue","darkgreen","purple","orange","darkblue","gray","green"]
    for i in range(1,11):
        dic_colores[str(i)] = colores[i-1]
    if option != "ALL":
        df["marker"] = [dic_colores[str(option)]]*len(df["marker"])
    else:    
        for i in range(5):
            olines = df['Línia / Línea'][df["ID"]==i].values[0]
            olines = olines.split(",")
            e = olines[0]
            df["marker"][i] = dic_colores[e]
    for i in range(5):
        index = df["Nom / Nombre"][df["ID"]==i].index[0]
        value = df["Nom / Nombre"][df["ID"]==i].values[0]
        texto = f"{index} {value}  Lines: {df['Línia / Línea'][df['Nom / Nombre'] == value].values[0]}"
        c = [df["Longitud"][df["ID"]==i],df["Latitud"][df["ID"]==i]]
        m = add_marker(m, c, color=df["marker"][i], text=texto) 
    with col2:
        st.write('Map of the nearest stations')
        st_data = st_folium(m, height=215)
    
    mas_cercanas=[]
    for index,row in df.head(5).iterrows():
        mas_cercanas.append(row['Nom / Nombre'])
        
    
    Origen = st.selectbox("Select one of the nearest stations:", mas_cercanas)
    
    nombre_seleccionado = st.selectbox("Enter a destination station:", nombres)
    # Almacenar en la variable destino
    Destino = nombre_seleccionado
    
    
    def distancia(lat1,lon1,lat2,lon2):
        distancia = geodesic((lat1,lon1),(lat2,lon2)).kilometers
        return distancia
    
    lineas=[{'ini':'Bétera','fin':'Castelló','linea':'1'},{'ini':'Torrent Avinguda','fin':'Llíria','linea':'2'},
            {'ini':'Aeroport','fin':'Rafelbunyol','linea':'3'},{'ini':'Dr. Lluch','fin':'Mas del Rosari','linea':'4'},
            {'ini':'Aeroport','fin':'Marítim','linea':'5'},{'ini':'Tossal del Rei','fin':'Marítim','linea':'6'},
            {'ini':'Torrent Avinguda','fin':'Marítim','linea':'7'},{'ini':'Marítim','fin':'Neptú','linea':'8'},
            {'ini':'Riba-roja de Túria','fin':'Alboraia Peris Aragó','linea':'9'},{'ini':'Alacant','fin':'Natzaret','linea':'10'}]    
     
    tuplas=[('Ll. Llarga - Terramelar','À Punt'),('Les Carolines - Fira','Vicent Andrés Estellés')]
    
    rutas=[]
    
    for i in range(len(lineas)):
        ruta=[]
        l_uno=lineas[i]
        parada=l_uno['ini']
        ruta.append(l_uno['ini'])
        for index,row in datos.iterrows():
            if l_uno['linea'] in row['Línia / Línea'].split(','):
                if (row['Nom / Nombre']==parada):
                    lat_ini,lon_ini=row['Latitud'],row['Longitud']
        min_dist=1000000
        while l_uno['fin'] not in ruta:
            for index,row in datos.iterrows():
                if l_uno['linea'] in row['Línia / Línea'].split(','):
                    if (row['Nom / Nombre']!=parada) and row['Nom / Nombre']not in ruta:
                        lat_fin,lon_fin=row['Latitud'],row['Longitud']
                        if (distancia(lat_ini,lon_ini,lat_fin,lon_fin))<min_dist:
                            min_dist=distancia(lat_ini,lon_ini,lat_fin,lon_fin)
                            lat_final,lon_final=lat_fin,lon_fin
                            parada=row['Nom / Nombre']
            ruta.append(parada)
            lat_ini,lon_ini=lat_final,lon_final
            min_dist=1000000
        rutas.append(ruta)
    
    # Crear un grafo vacío
    grafo = nx.Graph()
    
    # Ejemplo de lista de listas de rutas
    
    # Agregar las rutas como aristas al grafo
    for ruta in rutas:
        for j in range(len(ruta) - 1):
            origen = ruta[j]
            destino = ruta[j + 1]
            grafo.add_edge(origen, destino)
    for tupla in tuplas:
        grafo.add_edge(tupla[0],tupla[1])
        
    
    # Calcular todos los caminos más cortos entre dos sitios
    origen = Origen
    destino = Destino
    try:
        camino = nx.shortest_path(grafo, origen, destino)
    except:
        camino=[]
    if len(camino)>0:
        dic={}
        for index,row in datos.iterrows():
            if row['Nom / Nombre'] in camino:
                dic[row['Nom / Nombre']]=row['Línia / Línea'].split(',')
        dic2={}
        for parada in camino:
            dic2[parada]=dic[parada]
        
        
        
        visitadas=[]
        def mas_lejos(parada):
            pos=camino.index(parada)
            lineas=dic2[parada]
            inter=[]
            for i in range(pos,len(camino)):
                visitadas.append(camino[i])
                lineas2=dic2[camino[i]]
                interseccion = list(set(lineas).intersection(lineas2))
                if len(interseccion)==0:
                    return camino[i-1]
                    break
                    
        parada=camino[0]
        transbordos=[]
        while camino[-1] not in visitadas:
            stop=mas_lejos(parada)
            transbordos.append(stop)
            parada=stop
        
        for i in transbordos:
            if i is None:
                transbordos.remove(i)
        
        
        st.write(f'BEST ROUTE FROM {origen.upper()} TO {destino.upper()}')
        st.write('Number of stations:',len(camino))
        a=len(transbordos)
        if a>0:
            parada=camino[0]
            trayectos=[]
            i=0
            while a>0:
                lineas=[]
                sig=transbordos[i]
                for linea in dic2[parada]:
                    if linea in dic2[sig]:
                        lineas.append(linea)
                trayectos.append((parada,sig,lineas))
                parada=sig
                
                a-=1
                i+=1
            lineas_ult=[]
            transbordo_1=transbordos[-1]
            ultima=camino[-1]
            lineas_ult=[]
            for l in dic2[transbordo_1]:
                if l in dic2[ultima]:
                    lineas_ult.append(l)
            
            for i in range(len(trayectos)+1):
                try:
                    l2=trayectos[i][2]
                    lin=''
                    for j in range(len(trayectos[i][2])):
                        if j+1<len(trayectos[i][2]):
                            lin+=f'{trayectos[i][2][j]}, '
                        else: 
                            lin+=f'{trayectos[i][2][j]}'
                    st.write(f' {i+1}) From {trayectos[i][0]} to {transbordos[i]}, Line {lin}')
                    
                except: 
                    pass
            caden = ', '.join(lineas_ult)
            st.write(f' { i+1}) From {transbordo_1} to {ultima}, Line {caden}')
        else:
            disp=[]
            for i in dic2[Origen]:
                if i in dic2[Destino]:
                    disp.append(i)
            cadena = ', '.join(disp)
            st.write(f'1) From {Origen} to {Destino} Line {cadena[0]}')
    else:
        st.write(f"It is not possible to go from {Origen} to {Destino}.")
    
    
    
    
else:
    st.write("No se encontraron coordenadas para la dirección específica")