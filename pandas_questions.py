"""Plotting referendum results in pandas.

In short, we want to make beautiful map to report results of a referendum. In
some way, we would like to depict results with something similar to the maps
that you can find here:
https://github.com/x-datascience-datacamp/datacamp-assignment-pandas/blob/main/example_map.png

To do that, you will load the data as pandas.DataFrame, merge the info and
aggregate them by regions and finally plot them on a map using `geopandas`.
"""
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt


def load_data():
    """Load data from the CSV files referundum/regions/departments."""
    referendum = pd.read_csv('data/referendum.csv',sep=';')
    regions = pd.read_csv('data/regions.csv')
    departments = pd.read_csv('data/departments.csv')

    return referendum, regions, departments



def merge_regions_and_departments(regions, departments):
    """Merge regions and departments in one DataFrame.

    The columns in the final DataFrame should be:
    ['code_reg', 'name_reg', 'code_dep', 'name_dep']
    """
    merged_df = pd.merge(regions, departments, left_on='code', right_on='region_code', how='inner')
    merged_df = merged_df.rename(columns={
        'code_x': 'code_reg',
        'name_x': 'name_reg',
        'code_y': 'code_dep',
        'name_y': 'name_dep'
    })[['code_reg', 'name_reg', 'code_dep', 'name_dep']]
    return merged_df


def merge_referendum_and_areas(referendum, regions_and_departments):
    """Merge referendum and regions_and_departments in one DataFrame.

    You can drop the lines relative to DOM-TOM-COM departments, and the
    french living abroad, which all have a code that contains `Z`.

    DOM-TOM-COM departments are departements that are remote from metropolitan
    France, like Guadaloupe, Reunion, or Tahiti.
    """
    ref = referendum.copy()
    raf = regions_and_departments.copy()

    ref_code = ref["Department code"].astype(str).str.strip().str.upper()
    ref_code = ref_code.where(~(ref_code.str.len() == 1) | ~ref_code.str.isdigit(), '0' + ref_code)
    ref = ref.assign(code_dep_norm=ref_code)

    rad_code = raf['code_dep'].astype(str).str.strip().str.upper()
    rad_code = rad_code.where(~(rad_code.str.len() == 1) | ~rad_code.str.isdigit(), '0' + rad_code)
    rad = raf.assign(code_dep_norm=rad_code)

    merged = pd.merge(
        ref,
        rad,
        on='code_dep_norm',
        how='inner'
    )

    code_dep_clean = merged['code_dep'].astype(str).str.strip().str.upper()
    overseas_mask = (
        code_dep_clean.str.startswith('97') |
        code_dep_clean.str.startswith('98') |
        code_dep_clean.str.contains('Z', na=False)
    )
    merged = merged[~overseas_mask].copy()
    
    merged = merged.drop(columns=['code_dep_norm','code_dep_x'], errors='ignore')
    merged = merged.rename(columns={'code_dep_y': 'code_dep'}, errors='ignore')
    return merged


def compute_referendum_result_by_regions(referendum_and_areas):
    """Return a table with the absolute count for each region.

    The return DataFrame should be indexed by `code_reg` and have columns:
    ['name_reg', 'Registered', 'Abstentions', 'Null', 'Choice A', 'Choice B']
    """
    grouped = referendum_and_areas.groupby(['code_reg', 'name_reg']).agg({
        'Registered': 'sum',
        'Abstentions': 'sum',
        'Null': 'sum',
        'Choice A': 'sum',
        'Choice B': 'sum'
    }).reset_index()

    result_df = grouped.set_index('code_reg')
    return result_df



def plot_referendum_map(referendum_result_by_regions):
    """Plot a map with the results from the referendum.

    * Load the geographic data with geopandas from `regions.geojson`.
    * Merge these info into `referendum_result_by_regions`.
    * Use the method `GeoDataFrame.plot` to display the result map. The results
      should display the rate of 'Choice A' over all expressed ballots.
    * Return a gpd.GeoDataFrame with a column 'ratio' containing the results.
    """
    geo_df = gpd.read_file('data/regions.geojson')

    merged_geo_df = geo_df.merge(
        referendum_result_by_regions,
        left_on='code',
        right_index=True,
        how='inner'
    )

    merged_geo_df['ratio'] = merged_geo_df['Choice A'] / (merged_geo_df['Choice A'] + merged_geo_df['Choice B'])

    ax = merged_geo_df.plot(column='ratio', cmap='OrRd', legend=True, edgecolor='black')
    ax.set_title("Referendum Results by Region (Choice A Ratio)")

    return merged_geo_df


if __name__ == "__main__":

    referendum, df_reg, df_dep = load_data()
    regions_and_departments = merge_regions_and_departments(
        df_reg, df_dep
    )
    referendum_and_areas = merge_referendum_and_areas(
        referendum, regions_and_departments
    )
    referendum_results = compute_referendum_result_by_regions(
        referendum_and_areas
    )
    print(referendum_results)

    plot_referendum_map(referendum_results)
    plt.show()

