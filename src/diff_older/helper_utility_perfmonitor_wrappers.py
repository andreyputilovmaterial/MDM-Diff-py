

import time
import re



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
        self.config_text_pipein = config['report_text_pipein'] if 'report_text_pipein' in config and config['report_text_pipein'] else 'progress'
    
    def __iter__(self):
        self.progress = 0
        self.time_started = time.time()
        self.time_last_reported = self.time_started
        self.progress_last_reported = -1
        return self
    
    def _calc_eta(self,time_now=None):
        def calc_eta(time_start,time_now,records_expected_total,records_now):
            return (1*time_start+int((time_now-time_start)*(records_expected_total/records_now)))
        if self.userprovideddata_totalrecords is None:
            return None
        if not time_now:
            time_now = time.time()
        time_started = self.time_started
        return calc_eta(time_started,time_now,self.userprovideddata_totalrecords,self.progress)

    def __next__(self):
        def fmt_duration(seconds):
            def fmt(v):
                v = '{v}'.format(v=v)
                return re.sub(r'(\.[1-9]\d*?)[0]{3}\d*',lambda m: m[1],v,flags=re.I|re.DOTALL)
            if seconds<300:
                return '{n} seconds'.format(n=fmt(int(seconds)))
            else:
                if seconds<6000:
                    return '{n} minutes'.format(n=fmt(0.1*int(seconds/6)))
                else:
                    return '{n} hours'.format(n=fmt(0.1*int(seconds/360)))
        self.progress = self.progress + 1
        if (self.config_frequency_records is None) or (self.progress - self.progress_last_reported > self.config_frequency_records):
            time_now = time.time()
            if (self.config_frequency_timeinterval is None) or ((time_now - self.time_last_reported)>self.config_frequency_timeinterval):
                eta = self._calc_eta(time_now)
                print( '{text_pipe}: processing {nline}{display_out_total}{display_details}'.format(
                    nline = self.progress,
                    display_out_total = ' / {nlinetotal}'.format(nlinetotal=self.userprovideddata_totalrecords) if (self.userprovideddata_totalrecords is not None) else '',
                    display_details = ' ({per}%{details_eta})'.format(
                        per = round(self.progress*100/self.userprovideddata_totalrecords,1),
                        details_eta = ', remaining: {remaining}, ETA: {eta}'.format(
                            remaining = fmt_duration(eta-time_now),
                            eta = '{t}'.format(t=time.strftime('%m/%d/%Y %H:%M:%S',time.localtime(eta))),
                        ) if eta else '',
                    ) if (self.userprovideddata_totalrecords is not None) else '',
                    text_pipe = self.config_text_pipein,
                ))
                self.progress_last_reported = self.progress
                self.time_last_reported = time_now
        return None

