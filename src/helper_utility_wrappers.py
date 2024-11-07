

import time



class PerformanceMonitor:
    def __init__(self,config={}):
        self.__config = config
        self.progress = None
        self.time_started = None
        self.time_last_reported = None
        self.progress_last_reported = None
        self.userprovideddata_totalrecords = config['total_records'] if 'total_records' in config else None
        self.config_frequency_records = config['report_frequency_records_count'] if 'report_frequency_records_count' in config else None
        self.config_frequency_timeinterval = config['report_frequency_timeinterval'] if 'report_frequency_timeinterval' in config else None
    
    def __iter__(self):
        self.progress = 0
        self.time_started = time.time()
        self.time_last_reported = self.time_started
        self.progress_last_reported = -1
        return self
    
    def __next__(self):
        self.progress = self.progress + 1
        #pdb.set_trace()
        if (self.config_frequency_records is None) or (self.progress - self.progress_last_reported > self.config_frequency_records):
            time_now = time.time()
            if (self.config_frequency_timeinterval is None) or ((time_now - self.time_last_reported)>self.config_frequency_timeinterval):
                print( 'progress: processing {nline}{display_out_total}{display_percents}'.format(
                    nline = self.progress,
                    display_out_total = ' / {nlinetotal}'.format(nlinetotal=self.userprovideddata_totalrecords) if (self.userprovideddata_totalrecords is not None) else '',
                    display_percents=' ({per}%)'.format(per=round(self.progress*100/self.userprovideddata_totalrecords,1)) if (self.userprovideddata_totalrecords is not None) else ''
                ))
                self.progress_last_reported = self.progress
                self.time_last_reported = time_now
        return None

