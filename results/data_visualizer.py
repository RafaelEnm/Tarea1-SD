#!/usr/bin/env python3
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re
from pathlib import Path

# Intenta importar numpy, necesario para algunos gráficos avanzados
try:
    import numpy as np
except ImportError:
    print("ERROR: La dependencia 'numpy' no se encuentra. Por favor, añádela a requirements.txt")
    exit(1)

# Configuración del estilo de los gráficos
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# ... (La función generate_visualization se mantiene igual que antes) ...
def generate_visualization(dataframe, category, output_path):
    """Generates and saves a single visualization based on the category."""
    plt.figure(figsize=(12, 8))
    
    # --- Alert Frequency by Type ---
    if category == 'alert_frequency':
        top_data = dataframe.sort_values('quantity', ascending=False).head(8)
        ax = sns.barplot(data=top_data, y='alert_type', x='quantity', palette='viridis')
        plt.title('Top 8 Most Frequent Incident Types', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Number of Occurrences', fontsize=14)
        plt.ylabel('Incident Type', fontsize=14)
        ax.bar_label(ax.containers[0], padding=3, fontsize=11, fontweight='bold')

    # --- Hourly Distribution of Incidents ---
    elif category == 'hourly_distribution':
        df = dataframe.copy()
        df['hour_val'] = pd.to_numeric(df['hour'], errors='coerce').fillna(-1).astype(int)
        df = df.sort_values('hour_val').reset_index(drop=True)
        
        plt.plot(df.index, df['alert_count'], marker='o', linestyle='-', color='#4ECDC4', linewidth=2.5, markersize=6)
        plt.fill_between(df.index, df['alert_count'], alpha=0.3, color='#4ECDC4')
        plt.xticks(ticks=df.index, labels=df['hour'], rotation=45, ha='right')
        plt.title('Hourly Distribution of Incidents', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Hour of the Day', fontsize=14)
        plt.ylabel('Number of Incidents', fontsize=14)

    # --- Jam Count by Zone ---
    elif category == 'jam_count_by_zone':
        top_10 = dataframe.sort_values('jam_count', ascending=False).head(10)
        colors = plt.cm.Blues(np.linspace(0.4, 0.9, len(top_10)))
        ax = top_10.plot(kind='bar', x='city', y='jam_count', color=colors, legend=False)
        plt.title('Top 10 Zones with Highest Jam Count', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Urban Zone', fontsize=14)
        plt.ylabel('Number of Jams', fontsize=14)
        plt.xticks(rotation=45, ha='right')

    # --- Jam Length Distribution by Zone (Pie Chart) ---
    elif category == 'jam_length_by_zone':
        top_8 = dataframe.sort_values('total_length', ascending=False).head(8)
        plt.figure(figsize=(10, 10))
        colors = ['#FF9999', '#66B2FF', '#99FF99', '#FFCC99', '#FF99CC', '#99CCFF', '#FFB366', '#B3B3FF']
        wedges, texts, autotexts = plt.pie(top_8['total_length'], labels=top_8['city'], autopct='%1.1f%%',
                                           colors=colors, startangle=90, textprops={'fontsize': 12})
        plt.title('Proportional Jam Length by Zone', fontsize=16, fontweight='bold', pad=20)
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')

    # --- Sectors with Most Alerts ---
    elif category == 'top_alert_sectors':
        top_6 = dataframe.sort_values('alert_count', ascending=False).head(6)
        ax = sns.barplot(data=top_6, y='sector', x='alert_count', palette='magma')
        plt.title('Top 6 Sectors with Most Reports', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Total Reports', fontsize=14)
        plt.ylabel('Urban Sector', fontsize=14)
        ax.bar_label(ax.containers[0], padding=3, fontsize=11)

    # --- Critical Accident Sectors ---
    elif category == 'top_accident_sectors':
        top_5 = dataframe.sort_values('accident_count', ascending=False).head(5)
        colors = ['#8B0000', '#B22222', '#DC143C', '#FF6347', '#FFA07A'][::-1]
        ax = top_5.plot(kind='bar', x='sector', y='accident_count', color=colors, legend=False)
        plt.title('Top 5 Critical Accident Zones', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Urban Sector', fontsize=14)
        plt.ylabel('Number of Accidents', fontsize=14)
        avg = top_5['accident_count'].mean()
        plt.axhline(y=avg, color='red', linestyle='--', alpha=0.7, label=f'Average: {avg:.1f}')
        plt.legend()
        plt.xticks(rotation=45, ha='right')
        
    # --- Streets with Most Alerts ---
    elif category == 'top_alert_streets':
        top_8 = dataframe.sort_values('alert_count', ascending=False).head(8)
        top_8['street_short'] = top_8['street'].apply(lambda x: str(x)[:25] + '...' if len(str(x)) > 25 else str(x))
        ax = sns.barplot(data=top_8, x='street_short', y='alert_count', palette='rocket')
        plt.title('Top 8 Streets with Most Reports', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Street', fontsize=14)
        plt.ylabel('Number of Reports', fontsize=14)
        plt.xticks(rotation=45, ha='right')

    # --- High-Risk Streets (Polar Chart) ---
    elif category == 'top_accident_streets':
        top_6 = dataframe.sort_values('accident_count', ascending=False).head(6)
        plt.figure(figsize=(10, 10))
        ax = plt.subplot(111, projection='polar')
        theta = np.linspace(0, 2 * np.pi, len(top_6), endpoint=False)
        radii = top_6['accident_count']
        colors = plt.cm.Reds(np.linspace(0.4, 0.9, len(top_6)))
        bars = ax.bar(theta, radii, width=0.8, color=colors, alpha=0.8)
        ax.set_xticks(theta)
        ax.set_xticklabels([str(s)[:15] + '...' if len(str(s)) > 15 else str(s) for s in top_6['street']], fontsize=11)
        plt.title('Top 6 High-Risk Streets (Radial View)', fontsize=16, fontweight='bold', pad=30)

    else:
        plt.close()
        return

    plt.tight_layout()
    output_file = os.path.join(output_path, f"{category}.png")
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"OK: Chart '{category}' saved to: {output_file}")


def find_latest_execution_dir(base_dir):
    """Finds the most recent directory matching the 'ejecucion_*' pattern."""
    regex = re.compile(r'ejecucion_\d{8}_\d{6}$')
    dirs = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d)) and regex.match(d)]
    if not dirs:
        return None
    return sorted(dirs, reverse=True)[0]

def run_process():
    """Main process to find data and generate all visualizations."""
    results_dir = "/app/results"
    
    latest_exec_dir_name = find_latest_execution_dir(results_dir)
    if not latest_exec_dir_name:
        print("ERROR: No execution directories found in /app/results.")
        return

    work_dir = os.path.join(results_dir, latest_exec_dir_name)
    print(f"Processing data from directory: {work_dir}")

    plots_dir = os.path.join(work_dir, 'visualizations')
    os.makedirs(plots_dir, exist_ok=True)

    file_to_viz_map = {
        'alert_type_frequency.csv': 'alert_frequency',
        'peak_hours.csv': 'hourly_distribution',
        'jams_by_city.csv': ['jam_count_by_zone', 'jam_length_by_zone'],
        'sectors_with_most_alerts.csv': 'top_alert_sectors',
        'sectors_with_most_accidents.csv': 'top_accident_sectors',
        'streets_with_most_alerts.csv': 'top_alert_streets',
        'streets_with_most_accidents.csv': 'top_accident_streets',
    }

    print("\nStarting visualization generation...")
    for filename, viz_tasks in file_to_viz_map.items():
        file_path = os.path.join(work_dir, filename)
        if not os.path.exists(file_path):
            print(f"WARNING: Data file not found, skipping: {filename}")
            continue
        
        try:
            # --- CAMBIO CLAVE AQUÍ ---
            # Intentar leer el archivo CSV
            df = pd.read_csv(file_path)
            # Verificar si, después de leerlo, el DataFrame está vacío
            if df.empty:
                print(f"INFO: File '{filename}' is empty. Skipping visualization.")
                continue
            # --- FIN DEL CAMBIO ---

            if isinstance(viz_tasks, list):
                for task in viz_tasks:
                    generate_visualization(df, task, plots_dir)
            else:
                generate_visualization(df, viz_tasks, plots_dir)
        
        except pd.errors.EmptyDataError:
            # Capturar el error si el archivo está completamente vacío
            print(f"INFO: File '{filename}' is empty. Skipping visualization.")
            continue
        except Exception as e:
            # Capturar cualquier otro error inesperado
            print(f"ERROR processing {filename}: {e}")

    print(f"\nProcess complete. Visualizations saved in: {plots_dir}")

if __name__ == "__main__":
    run_process()