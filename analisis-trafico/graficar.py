#!/usr/bin/env python3
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re
from pathlib import Path

# Configurar estilo de matplotlib
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def generar_visualizacion(datos, categoria, ruta_destino):
    # Configuración de figura más compacta
    plt.figure(figsize=(12, 8))
    
    if categoria == 'frecuencia_tipos_alertas':
        # Mostrar solo top 8 y usar gráfico horizontal para mejor legibilidad
        top_datos = datos.sort_values('cantidad', ascending=False).head(8)
        ax = top_datos.plot(kind='barh', x='tipo_alerta', y='cantidad', color='#FF6B6B')
        plt.title('Top 8 - Tipos de Incidentes Más Frecuentes', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Número de Ocurrencias', fontsize=14)
        plt.ylabel('Tipo de Incidente', fontsize=14)
        
        # Agregar valores en las barras
        for i, v in enumerate(top_datos['cantidad']):
            ax.text(v + max(top_datos['cantidad'])*0.01, i, str(v), 
                   va='center', fontweight='bold', fontsize=11)
        
    elif categoria == 'distribucion_horaria':
        datos = datos.copy()
        datos['etiqueta_hora'] = datos['hora'].fillna('Sin hora')
        
        def procesar_hora(valor):
            try:
                if pd.isna(valor) or valor == '':
                    return -1
                return int(valor)
            except (ValueError, TypeError):
                return -1
        
        datos['numero_hora'] = datos['hora'].apply(procesar_hora)
        datos = datos.sort_values('numero_hora')
        
        # Usar gráfico de línea para tendencias temporales
        plt.plot(range(len(datos)), datos['cantidad_alertas'], 
                marker='o', linewidth=2.5, markersize=6, color='#4ECDC4')
        plt.fill_between(range(len(datos)), datos['cantidad_alertas'], alpha=0.3, color='#4ECDC4')
        plt.xticks(range(len(datos)), datos['etiqueta_hora'], rotation=45)
        plt.grid(True, linestyle='--', alpha=0.4)
        plt.title('Distribución Horaria de Incidentes', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Hora del Día', fontsize=14)
        plt.ylabel('Cantidad de Incidentes', fontsize=14)
        
    elif categoria == 'congestiones_cantidad':
        # Reducir a top 10 y usar colores degradados
        top_10 = datos.sort_values('num_atascos', ascending=False).head(10)
        colors = plt.cm.Blues(np.linspace(0.4, 0.8, len(top_10)))
        ax = top_10.plot(kind='bar', x='ciudad', y='num_atascos', color=colors)
        plt.title('Top 10 - Zonas con Mayor Congestión', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Zona Urbana', fontsize=14)
        plt.ylabel('Cantidad de Congestiones', fontsize=14)
        
        # Mostrar solo cada 2da etiqueta en X para evitar sobreposición
        ax.set_xticks(range(0, len(top_10), 2))
        ax.set_xticklabels([top_10.iloc[i]['ciudad'] for i in range(0, len(top_10), 2)])
        
    elif categoria == 'congestiones_longitud':
        # Top 8 con gráfico de pastel para proporciones
        top_8 = datos.sort_values('largo_total', ascending=False).head(8)
        plt.figure(figsize=(10, 10))
        
        # Colores personalizados
        colors = ['#FF9999', '#66B2FF', '#99FF99', '#FFCC99', 
                 '#FF99CC', '#99CCFF', '#FFB366', '#B3B3FF']
        
        wedges, texts, autotexts = plt.pie(top_8['largo_total'], 
                                          labels=top_8['ciudad'],
                                          autopct='%1.1f%%',
                                          colors=colors,
                                          startangle=90)
        
        plt.title('Distribución de Extensión de Congestión por Zona', 
                 fontsize=16, fontweight='bold', pad=20)
        
        # Mejorar legibilidad de los textos
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
    elif categoria == 'sectores_alertas_max':
        # Top 6 con gráfico horizontal
        top_6 = datos.sort_values('cantidad_alertas', ascending=False).head(6)
        ax = top_6.plot(kind='barh', x='comuna', y='cantidad_alertas', color='#DDA0DD')
        plt.title('Top 6 - Sectores con Más Reportes', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Total de Reportes', fontsize=14)
        plt.ylabel('Sector Urbano', fontsize=14)
        
        # Agregar valores
        for i, v in enumerate(top_6['cantidad_alertas']):
            ax.text(v + max(top_6['cantidad_alertas'])*0.01, i, str(v), 
                   va='center', fontweight='bold')
        
    elif categoria == 'sectores_siniestros_max':
        # Top 5 con indicadores de gravedad por color
        top_5 = datos.sort_values('cantidad_accidentes', ascending=False).head(5)
        
        # Colores de riesgo (rojo más intenso para mayor cantidad)
        colors = ['#8B0000', '#B22222', '#DC143C', '#FF6347', '#FFA07A']
        
        ax = top_5.plot(kind='bar', x='comuna', y='cantidad_accidentes', color=colors)
        plt.title('Top 5 - Zonas Críticas de Siniestralidad', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Sector Urbano', fontsize=14)
        plt.ylabel('Número de Siniestros', fontsize=14)
        
        # Línea de referencia para el promedio
        promedio = top_5['cantidad_accidentes'].mean()
        plt.axhline(y=promedio, color='red', linestyle='--', alpha=0.7, 
                   label=f'Promedio: {promedio:.1f}')
        plt.legend()
        
    elif categoria == 'vias_alertas_max':
        # Top 8 con mejor formato de nombres
        top_8 = datos.sort_values('cantidad_alertas', ascending=False).head(8)
        
        # Acortar nombres muy largos
        top_8_copy = top_8.copy()
        top_8_copy['calle_corta'] = top_8_copy['calle'].apply(
            lambda x: x[:20] + '...' if len(str(x)) > 20 else x
        )
        
        ax = top_8_copy.plot(kind='bar', x='calle_corta', y='cantidad_alertas', color='#E74C3C')
        plt.title('Top 8 - Vías con Más Reportes', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Arteria Vial', fontsize=14)
        plt.ylabel('Cantidad de Reportes', fontsize=14)
        
    elif categoria == 'vias_siniestros_max':
        # Top 6 con gráfico radial (polar)
        top_6 = datos.sort_values('cantidad_accidentes', ascending=False).head(6)
        
        plt.figure(figsize=(10, 10))
        ax = plt.subplot(111, projection='polar')
        
        # Ángulos para cada barra
        theta = np.linspace(0, 2*np.pi, len(top_6), endpoint=False)
        radii = top_6['cantidad_accidentes']
        
        # Colores degradados
        colors = plt.cm.Reds(np.linspace(0.4, 0.9, len(top_6)))
        
        bars = ax.bar(theta, radii, width=0.8, color=colors, alpha=0.8)
        
        # Etiquetas
        ax.set_xticks(theta)
        ax.set_xticklabels([str(calle)[:15] + '...' if len(str(calle)) > 15 
                           else str(calle) for calle in top_6['calle']], 
                          fontsize=10)
        
        plt.title('Top 6 - Vías de Mayor Riesgo\n(Vista Radial)', 
                 fontsize=16, fontweight='bold', pad=30)
    
    # Configuración común para todos los gráficos
    if categoria != 'congestiones_longitud' and categoria != 'vias_siniestros_max':
        plt.xticks(rotation=45, ha='right', fontsize=11)
    
    plt.tight_layout()
    
    # Guardar con mayor calidad
    archivo_salida = os.path.join(ruta_destino, f"{categoria}.png")
    plt.savefig(archivo_salida, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Gráfico {categoria} optimizado y guardado en: {archivo_salida}")

def buscar_archivos_datos(carpeta):
    lista_archivos = []
    for directorio_raiz, _, archivos in os.walk(carpeta):
        for archivo in archivos:
            if archivo.endswith('.csv') and not archivo.startswith('encabezado'):
                lista_archivos.append(os.path.join(directorio_raiz, archivo))
    return lista_archivos

def ejecutar_proceso():
    carpeta_resultados = "/app/results"
    
    expresion_regular = re.compile(r'ejecucion_\d{8}_\d{6}$')
    carpetas_disponibles = [directorio for directorio in os.listdir(carpeta_resultados) 
                           if os.path.isdir(os.path.join(carpeta_resultados, directorio)) and 
                           expresion_regular.match(directorio)]
    
    if not carpetas_disponibles:
        print("ERROR: No se encontraron directorios de ejecución.")
        return
    
    carpetas_disponibles.sort(reverse=True)
    carpeta_trabajo = os.path.join(carpeta_resultados, carpetas_disponibles[0])
    print(f"PROCESANDO DIRECTORIO: {carpeta_trabajo}")
    
    carpeta_imagenes = os.path.join(carpeta_trabajo, 'visualizaciones_optimizadas')
    os.makedirs(carpeta_imagenes, exist_ok=True)
    
    archivos_datos = buscar_archivos_datos(carpeta_trabajo)
    
    if not archivos_datos:
        print("ERROR: No se encontraron archivos CSV para analizar.")
        return
    
    print("INICIANDO GENERACIÓN DE VISUALIZACIONES OPTIMIZADAS...")
    
    for ruta_archivo in archivos_datos:
        try:
            identificador_archivo = Path(ruta_archivo).stem.lower()
            
            if 'tipos_alerta_frecuencia' in identificador_archivo:
                tipo_visualizacion = 'frecuencia_tipos_alertas'
            elif 'horas_pico' in identificador_archivo:
                dataframe = pd.read_csv(ruta_archivo)
                generar_visualizacion(dataframe, 'distribucion_horaria', carpeta_imagenes)
                continue
            elif 'atascos_por_ciudad' in identificador_archivo:
                dataframe = pd.read_csv(ruta_archivo)
                generar_visualizacion(dataframe, 'congestiones_cantidad', carpeta_imagenes)
                generar_visualizacion(dataframe, 'congestiones_longitud', carpeta_imagenes)
                continue
            elif 'comunas_con_mas_alertas' in identificador_archivo:
                tipo_visualizacion = 'sectores_alertas_max'
            elif 'comunas_con_mas_accidentes' in identificador_archivo:
                tipo_visualizacion = 'sectores_siniestros_max'
            elif 'calles_con_mas_alertas' in identificador_archivo:
                tipo_visualizacion = 'vias_alertas_max'
            elif 'calles_con_mas_accidentes' in identificador_archivo:
                tipo_visualizacion = 'vias_siniestros_max'
            else:
                print(f"ADVERTENCIA: No se reconoce el tipo de archivo: {identificador_archivo}")
                continue
            
            dataframe = pd.read_csv(ruta_archivo)
            generar_visualizacion(dataframe, tipo_visualizacion, carpeta_imagenes)
                
        except Exception as error:
            print(f"ERROR al procesar {ruta_archivo}: {error}")
    
    print(f"PROCESO COMPLETADO: Visualizaciones generadas en {carpeta_imagenes}")

if __name__ == "__main__":
    # Importar numpy si no está disponible
    try:
        import numpy as np
    except ImportError:
        print("INSTALANDO DEPENDENCIA: numpy...")
        os.system("pip install numpy")
        import numpy as np
    
    ejecutar_proceso()