



CONFIG_NUM_COLUMNS_CONSIDERED_DIFFICULT = 1000
CONFIG_NUM_ROWS_CONSIDERED_DIFFICULT = 3000





def assess_difficulty(metric,data_left,data_right,config):
    if metric == 'global_col_count':
        try:
            if len(data_left['report_scheme']['columns'])>CONFIG_NUM_COLUMNS_CONSIDERED_DIFFICULT or len(data_right['report_scheme']['columns'])>CONFIG_NUM_COLUMNS_CONSIDERED_DIFFICULT:
                return True
        except:
            pass
    elif metric == 'col_count':
        try:
            if  ( (len(data_left)>CONFIG_NUM_COLUMNS_CONSIDERED_DIFFICULT) or (len(data_right)>CONFIG_NUM_COLUMNS_CONSIDERED_DIFFICULT) ):
                return True
        except:
            pass
    elif metric == 'row_count':
        try:
            if ( (len(data_left)>CONFIG_NUM_ROWS_CONSIDERED_DIFFICULT) or (len(data_right)>CONFIG_NUM_ROWS_CONSIDERED_DIFFICULT) ):
                return True
        except:
            pass
    else:
        raise NotImplementedError(f'detect difficulty: unknown metric: {metric}')
    return False

