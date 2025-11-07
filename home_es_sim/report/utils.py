import pandas as pd
import numpy as np
import pprint

import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.ticker as mticker
from blume.table import table

from .. import utils as project
from .. import grid, load, source, storage, location


import logging
logger = logging.getLogger(__name__)

# https://github.com/lgienapp/aquarel
from aquarel import load_theme
theme = load_theme("arctic_light")
theme.apply()
_edgecolour = "#d8dee9"
_bgcolour = "#eceff4"


def get_frame(year=None) -> pd.DataFrame:
    df = pd.DataFrame()
    #df = source_pv.get_frame(year=year)
    return df


def get_slug() -> str:
    slug = project.get_slug() + '_simulation'
    project.add_slug(slug=slug, name='Simulation')
    return slug


def get_list() -> []:
    return project.get_params()['report']


def get_year(name: str) -> int:
    return get_list(name)['year']


def get_page():
    # A4: (8.27,11.69)
    # PPT: (13.33,7.5)
    fig = plt.figure(
        layout="constrained", 
        figsize=(13.33,7.5), 
    )
    return fig


def get_frontpage_layout():
    fig = get_page()
    ax = fig.subplot_mosaic(
        [
            ['title','title','title'], 
            ['.','info','.'] 
        ],
        gridspec_kw={
            'left':0.05,
            'right':0.95,
            'bottom':0.2,
            'top':0.8, 
            'height_ratios':[
                1,
                2
            ]
        }
    )

    ax['title'].axis('off')
    ax['info'].axis('off')
    
    return fig, ax


def get_compose_layout():
    fig = get_page()
    ax = fig.subplot_mosaic(
        [
            ['monthly','monthly'], 
            ['legend','legend'], 
            ['energy', 'npv'], 
            ['cost', 'battery']
        ],
        gridspec_kw={
            'left':0.05,
            'right':0.95,
            'bottom':0.02,
            'top':0.9, 
            'height_ratios':[
                1,
                0.15,
                0.4,
                0.3
            ]
        }
    )

    ax['monthly'].set_title('Monthly energy [kWh]', fontsize='medium')
    ax['energy'].set_title('Total annual energy [kWh]', fontsize='medium')
    ax['cost'].set_title('Annual energy cost', fontsize='medium')
    ax['npv'].set_title('Investment', fontsize='medium')
    ax['battery'].set_title('Battery statistics', fontsize='medium')
    
    ax['legend'].axis('off')
    ax['energy'].axis('off')
    ax['cost'].axis('off')
    ax['npv'].axis('off')
    ax['battery'].axis('off')
    
    return fig, ax


def get_overview_layout():
    fig = get_page()
    ax = fig.subplot_mosaic(
        [
            ['cost','energy'], 
            ['nv','nnv'], 
            ['legend', 'legend']
        ],
        gridspec_kw={
            'left':0.05,
            'right':0.95,
            'bottom':0.02,
            'top':0.9, 
            'height_ratios':[
                1,
                1,
                0.5
            ]
        }
    )

    ax['energy'].set_title('Total annual energy import / export [kWh]', fontsize='medium')
    ax['cost'].set_title('Annual energy cost', fontsize='medium')
    ax['nv'].set_title('Present value', fontsize='medium')
    ax['nnv'].set_title('Net present value', fontsize='medium')
    
    ax['legend'].axis('off')
    
    return fig, ax


def get_compare_layout():
    fig = get_page()
    ax = fig.subplot_mosaic(
        [
            ['monthly','legend'], 
            ['dayhour','annual']
        ],
        gridspec_kw={
            'left':0.05,
            'right':0.95,
            'bottom':0.02,
            'top':0.9, 
            'height_ratios':[
                1,
                1
            ]
        }
    )

    ax['monthly'].set_title('Monthly yield [kWh]', fontsize='medium')
    ax['dayhour'].set_title('Dayhour (UTC) average yield [kWh]', fontsize='medium')
    ax['annual'].set_title('Annual yield [kWh]', fontsize='medium')
    
    ax['legend'].axis('off')
    ax['annual'].axis('off')
    
    return fig, ax


def get_colors(n):
    # https://matplotlib.org/stable/gallery/color/colormap_reference.html#sphx-glr-gallery-color-colormap-reference-py
    # https://stackoverflow.com/questions/72287305/matplotlib-convert-colormap-to-pastel-colors
    c=0.15
    colors = (1. - c) * plt.get_cmap("vanimo")(np.linspace(0, 1, n)) + c * np.ones((n, 4)) #rainbow
    return colors


def get_empty_yearhour_frame(year: int) -> pd.DataFrame:
    start = str(year) + '-01-01 00:00:00'
    end = str(year) + '-12-31 00:00:00'
    df = pd.DataFrame(index=pd.date_range(start=start, end=end, freq='1h', tz='utc'))
    df.index.name='time_utc'
    return df


def do_compose(year: int, params: dict) -> pd.DataFrame:
    df = get_empty_yearhour_frame(year)
    c = params

    try:
        c['grid']
    except:
        df['grid_import_price'] = 0
        df['grid_export_price'] = 0
    else:
        df_c = grid.get_frame(year=year, params=c['grid'])
        df = pd.concat([df, df_c], axis=1)

    try:
        c['source']
    except:
        df['source'] = 0
    else:
        df_c = source.get_frame(year=year, params=c['source'])
        df = pd.concat([df, df_c], axis=1)

    try:
        c['load']
    except:
        df['load'] = 0
    else:
        df_c = load.get_frame(year=year, params=c['load'])
        df = pd.concat([df, df_c], axis=1)
        
    try:
        c['storage']
    except:
        c['storage'] = 0
    else:
        df_c = storage.get_frame(year=year, params=c['storage'])
        df = pd.concat([df, df_c], axis=1)

    return df


def do_simulate(year: int, params: dict, data: pd.DataFrame) -> pd.DataFrame:
    df = get_empty_yearhour_frame(year)
    c = params

    try:
        c['grid']
    except:
        pass
    else:
        df_c = grid.do_simulate(year=year, params=c['grid'], data=data)
        df = pd.concat([df, df_c], axis=1)

    try:
        c['source']
    except:
        pass
    else:
        df_c = source.do_simulate(year=year, params=c['source'], data=data)
        df = pd.concat([df, df_c], axis=1)

    try:
        c['load']
    except:
        pass
    else:
        df_c = load.do_simulate(year=year, params=c['load'], data=data)
        df = pd.concat([df, df_c], axis=1)

    try:
        c['storage']
    except:
        pass
    else:
        df_c = storage.do_simulate(year=year, params=c, data=data)
        df = pd.concat([df, df_c], axis=1)

    return df


# https://sv.wikipedia.org/wiki/Nuv%C3%A4rdesmetoden#%C3%85terkommande_belopp
_npv_grid_cost = {}

def set_npv_grid_cost(name, df):
    global _npv_grid_cost
    _npv_grid_cost[name] = df['grid_cost'].sum()

def get_npv(name: str, npv: dict):
    #pprint.pprint(npv)
    norm = npv['compare']['name']
    G = npv['investment']
    a = _npv_grid_cost[norm] - _npv_grid_cost[name]
    p = npv['discount rate']
    n = npv['time']
    nv = a*(1/p - 1/(p*pow(1+p,n)))
    nnv = nv - G
    #nv = int(nv)
    #nnv = int(nnv)

    return a, nv, nnv


def do_report() -> []:
    res = []

    with PdfPages(project.get_outputfile()) as pdf:

        ###############################
        ###############################
        ###############################
        # Front page

        fig, ax = get_frontpage_layout();
        
        loc = location.get_location()
        
        ax['title'].text(
            0.5,0,
            loc['name'],
            fontsize='xx-large',
            horizontalalignment='center',
            verticalalignment='top',
            #transform=ax.transAxes
        )
        
        del loc['name']
        d = pd.DataFrame.from_dict(loc, orient='index')
        d = d.reset_index()
        t = table(ax['info'], cellText=d.to_numpy(), loc='upper center', edgeColour=_edgecolour, edges='BT')
        
        pdf.savefig()
        plt.close()       

        ###############################
        ###############################
        ###############################
        # Calculations

        df_res = pd.DataFrame()

        report_list = get_list()
        if report_list == None:
            report_list = []
            

        for r in report_list:
            year = r['year']
            name = r['name']

            df = get_empty_yearhour_frame(year)
            df_rep = pd.DataFrame(columns=['label',name + ' ' + str(year)]) #.from_dict({}, orient='index')

            try:
                r['compose']
            except:
                pass
            else:
                df_c = do_compose(year=year, params=r['compose'])
                df = pd.concat([df, df_c], axis=1)

            try:
                r['simulate']
            except:
                # default simulation is load - source
                df['grid_import_energy'] = df['load']
                df['grid_import_energy'] -= df['source']
                df['grid_export_energy'] = -df.where(df['grid_import_energy'] < 0, 0)['grid_import_energy']
                df['grid_import_energy'] = df.where(df['grid_import_energy'] > 0, 0)['grid_import_energy']
            else:
                df_s = do_simulate(year=year, params=r['simulate'], data=df)
                df = pd.concat([df, df_s], axis=1)


            df['grid_import_cost'] = df['grid_import_energy'] * df['grid_import_price']
            df['grid_export_revenue'] = df['grid_export_energy'] * df['grid_export_price']
            df['grid_cost'] = df['grid_import_cost'] - df['grid_export_revenue']
            

            set_npv_grid_cost(name=name, df=df)
            nv = None
            nnv = None
            savings = None
            addsavings = None

            try:
                r['npv']
            except:
                pass
            else:
                savings, nv, nnv = get_npv(name=name, npv=r['npv'])
                try:
                    addsavings = r['npv']['addsavings']
                except:
                    pass
                else:
                    savings += addsavings


            ###############################
            ###############################
            ###############################
            # Configurations


            fig, ax = get_compose_layout();
            fig.suptitle(name + ' (' + str(year) + ')')
            
            legend = {}

            d = df.groupby(df.index.month).sum()

            values = [
                'grid_import_energy',
                'load',
                'battery_charge_energy',
                'battery_discharge_energy',
                'source',             
                'grid_export_energy'
                ]

            colors = get_colors(len(values))
            width=1/(len(values)+1)
            multiplier = 0

            for v, c in zip(values, colors):
                offset = - width * (len(values)-1) / 2 + width * multiplier
                try:
                    d[v]
                except:
                    pass
                else:
                    legend[v] = c
                    ax['monthly'].bar(data=d, x=d.index + offset, width=width, height=v, color=c)
                multiplier += 1

            ax['monthly'].set_xticks(d.index)

            # add the legend
            patches = [Patch(color=v, label=k) for k, v in legend.items()]
            ax['legend'].axis('off')
            ax['legend'].legend(handles=patches, loc='upper left', ncol=3, fontsize='small', facecolor=_bgcolour, edgecolor=_edgecolour)

            # add the table
            d = df.sum().astype(int)
            d.drop(index=[
                'grid_import_price',
                'grid_export_price',
                'grid_import_cost',
                'grid_export_revenue',
                'grid_cost'],
                inplace=True)

            df_rep.loc[len(df_rep.index)] = ['Energy: Annual grid import', d['grid_import_energy']]
            df_rep.loc[len(df_rep.index)] = ['Energy: Annual grid export', d['grid_export_energy']]

            batt_annual_cycles = None
            try:
                d.drop(index=
                    'battery_soc_energy',
                    inplace=True)
            except:
                pass
            else:
                batt_capacity = r['simulate']['storage']['battery']['capacity']
                batt_energy_roundtrip = d['battery_charge_energy'].sum() + d['battery_discharge_energy'].sum()
                batt_annual_cycles = int((batt_energy_roundtrip/2)/batt_capacity)
                d.drop(index=[
                    'battery_charge_energy',
                    'battery_discharge_energy'],
                    inplace=True)

            d = d.reset_index() # move index to column so .to_numpy() works as we want
            max_hourly_mean_import_power = round(df['grid_import_energy'].max(), 2)
            max_hourly_mean_export_power = round(df['grid_export_energy'].max(), 2)
            d.loc[len(d.index)] = ['Max hourly mean grid import power', max_hourly_mean_import_power]
            d.loc[len(d.index)] = ['Max hourly mean grid export power', max_hourly_mean_export_power]

            t = table(ax['energy'], cellText=d.to_numpy(), loc='upper center', edgeColour=_edgecolour, edges='BT')#, cellLoc="left") , colLabels=d.index.values.tolist()

            d = df[['grid_cost', 'grid_import_cost', 'grid_export_revenue']]
            d = d.sum().astype(int)
            df_rep.loc[len(df_rep.index)] = ['Cost: Annual grid energy cost', d['grid_cost']]
            d = d.reset_index() # move index to column so .to_numpy() works as we want
            t = table(ax['cost'], cellText=d.values, loc='upper center', edgeColour=_edgecolour, edges='BT')#, cellLoc="left") colLabels=d.keys(),


            if not nv == None:
                npv_d = r['npv']
                del npv_d['compare']
                d = pd.DataFrame.from_dict(r['npv'], orient='index')
                d = d.reset_index() # move index to column so .to_numpy() works as we want
                d.loc[len(d.index)] = ['Annual savings', round(savings,0)]
                d.loc[len(d.index)] = ['Present value', round(nv,0)]
                d.loc[len(d.index)] = ['Net present value', round(nnv,0)]
                t = table(ax['npv'], cellText=d.to_numpy(), loc='upper center', edgeColour=_edgecolour, edges='BT')#, cellLoc="left") colLabels=d.keys(), 
                
                df_rep.loc[len(df_rep.index)] = ['Investment: Present value', round(nv,0)]
                df_rep.loc[len(df_rep.index)] = ['Investment: Net present value', round(nnv,0)]
            else:
                ax['npv'].set_title('')


            if not batt_annual_cycles == None:
                d = pd.DataFrame(columns=['a','b']) #.from_dict({}, orient='index')
                d.loc[len(d.index)] = ['Annual cycles', batt_annual_cycles]
                df_rep.loc[len(df_rep.index)] = ['Battery: annual cycles', int(batt_annual_cycles)]

                battery_charge_energy = int(round(df['battery_charge_energy'].sum(), 0))
                battery_discharge_energy = int(round(df['battery_discharge_energy'].sum(), 0))
                d.loc[len(d.index)] = ['battery_charge_energy', battery_charge_energy]
                d.loc[len(d.index)] = ['battery_discharge_energy', battery_discharge_energy]

                if not nv == None:
                    d.loc[len(d.index)] = ['Cycles over \'investment time\'', npv_d['time'] * batt_annual_cycles]
                t = table(ax['battery'], cellText=d.to_numpy(), loc='upper center', edgeColour=_edgecolour, edges='BT')#, cellLoc="left") colLabels=d.keys(), 
            else:
                ax['battery'].set_title('')


            pdf.savefig()  # saves the current figure into a pdf page
            plt.close()

            df_rep.set_index('label', inplace=True, drop=True)
            df_res = pd.concat([df_res, df_rep], axis=1)

            res.append(df)
        

        #########################################
        #########################################
        #########################################
        # Configuration comparision

        if len(report_list) > 0:
            fig, ax = get_overview_layout();
            fig.suptitle('Comparison')

            legend = {}

            d = df_res.transpose()

            values = d.index.array
            colors = get_colors(len(values))

            da = d
            da['Energy: Annual grid export'] = -da['Energy: Annual grid export']

            ax['cost'].bar(data=da, x=values, height=da['Cost: Annual grid energy cost'], color=colors)
            ax['energy'].bar(data=da, x=values, height=da['Energy: Annual grid import'], color=colors) # + offset
            ax['energy'].bar(data=da, x=values, height=da['Energy: Annual grid export'], color=colors, alpha=0.8) # + offset
            ax['nv'].bar(data=da, x=values, height=da['Investment: Present value'], color=colors)
            ax['nnv'].bar(data=da, x=values, height=da['Investment: Net present value'], color=colors)

            ax['cost'].set_xticklabels([])
            ax['energy'].set_xticklabels([])
            ax['nv'].set_xticklabels([])
            ax['nnv'].set_xticklabels([])

            #for container in ax['cost'].containers:
                #ax['cost'].bar_label(container, fmt='%.0f', padding=3) #, label_type='center')
            
            # add the legend
            patches = [Patch(color=v, label=k) for k, v in zip(values, colors)]
            ax['legend'].legend(handles=patches, loc='upper left', ncol=1, fontsize='small', facecolor=_bgcolour, edgecolor=_edgecolour)

            pdf.savefig()
            plt.close()


        #########################################
        #########################################
        #########################################
        # Source comparision

        systems = source.get_frames()

        if len(systems) > 0:
            fig, ax = get_compare_layout();
            fig.suptitle('Source systems comparision')

            colors = get_colors(len(systems))
            legend = {}
            pv_yield = {}

            for p, c in zip(systems.keys(), colors):
                legend[p] = c
                source_pv_df = systems[p]

                d = source_pv_df.groupby(source_pv_df.index.month).sum()
                ax['monthly'].step(data=d, x=d.index, y='source', color=c, where='mid', linewidth=2.5)
                ax['monthly'].set_xticks(d.index)
                ax['monthly'].xaxis.set_minor_locator(mticker.NullLocator())

                d = source_pv_df.groupby(source_pv_df.index.hour).mean()
                ax['dayhour'].step(data=d, x=d.index, y='source', color=c, where='mid', linewidth=2.5)
                ax['dayhour'].set_xticks(d.index)
                ax['dayhour'].xaxis.set_minor_locator(mticker.NullLocator())
                
                pv_yield[p] = source_pv_df.sum().astype(int)

            # add the table
            df = pd.DataFrame.from_dict(pv_yield, orient='index')
            df = df.reset_index()
            t = table(ax['annual'], cellText=df.values, loc='upper center', edgeColour=_edgecolour, edges='BT')

            # add the legend
            patches = [Patch(color=v, label=k) for k, v in legend.items()]
            ax['legend'].legend(handles=patches, loc='upper left', ncol=1, fontsize='small', facecolor=_bgcolour, edgecolor=_edgecolour)

            pdf.savefig()
            plt.close()

    return res