
import sys, os
import json, re
from datetime import datetime




def val(s):
    if re.match(r'[<>]',re.sub(r'(?:<<(?:ADDED|ENDADDED|REMOVED|ENDREMOVED)>>|&#60;&#60;HIDDENLINEBREAK&#62;&#62;)','',s)):
        raise Exception('Create HTML report: Field values should already be escaped in Json. Some field contains "<" or ">". Please revise: {field}'.format(field=s))
    return re.sub(r'<<ADDED>>','<span class="mdmdiff-inlineoverlay-added">',re.sub(r'<<REMOVED>>','<span class="mdmdiff-inlineoverlay-removed">',re.sub(r'<<(?:ENDADDED|ENDREMOVED)>>','</span>',re.sub(r'&#60;&#60;HIDDENLINEBREAK&#62;&#62;','<!-- HIDDENLINEBREAK --><br />',s))))


def create_html(report):

    fields_is_mdmreport = ( re.match(r'^\s*?true\s*?$',report['MDMREPSCRIPT']) )

    fields_mdmreporttype = val(report['ReportType'])

    fields_mdmreporttype_allowed = ['MDDFields','MDDDiff','MDDSTK']
    if not fields_mdmreporttype in fields_mdmreporttype_allowed:
        raise Exception('The report type is "{val}" and is not recognized; allowed are only {types}'.format(val=fields_mdmreporttype,types=','.join(fields_mdmreporttype_allowed)))

    if not fields_is_mdmreport:
        raise Exception("JSON does not pass validation")

    # fields_MDD = val(report['MDD'])
    fields_File_ReportTitle = val(report['FileProperties']['ReportTitle']) if (('FileProperties' in report) and ('ReportTitle' in report['FileProperties'])) else 'MDD Diff'
    fields_File_ReportHeading = val(report['FileProperties']['ReportHeading']) if (('FileProperties' in report) and ('ReportHeading' in report['FileProperties'])) else 'MDD Diff'
    fields_File_ReportInfo = report['FileProperties']['ReportInfo'] if (('FileProperties' in report) and ('ReportInfo' in report['FileProperties'])) else ['']

    TEMPLATE_HTML_CSS_NORMALIZECSS = """
article,aside,details,figcaption,figure,footer,header,hgroup,nav,section,summary{display:block;}audio,canvas,video{display:inline-block;*display:inline;*zoom:1;}audio:not([controls]){display:none;height:0;}[hidden]{display:none;}html{font-size:100%;-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%;}html,button,input,select,textarea{font-family:sans-serif;}body{margin:0;}a:focus{outline:thin dotted;}a:active,a:hover{outline:0;}h1{font-size:2em;margin:0.67em 0;}h2{font-size:1.5em;margin:0.83em 0;}h3{font-size:1.17em;margin:1em 0;}h4{font-size:1em;margin:1.33em 0;}h5{font-size:0.83em;margin:1.67em 0;}h6{font-size:0.75em;margin:2.33em 0;}abbr[title]{border-bottom:1px dotted;}b,strong{font-weight:bold;}blockquote{margin:1em 40px;}dfn{font-style:italic;}mark{background:#ff0;color:#000;}p,pre{margin:1em 0;}code,kbd,pre,samp{font-family:monospace,serif;_font-family:'courier new',monospace;font-size:1em;}pre{white-space:pre;white-space:pre-wrap;word-wrap:break-word;}q{quotes:none;}q:before,q:after{content:'';content:none;}small{font-size:75%;}sub,sup{font-size:75%;line-height:0;position:relative;vertical-align:baseline;}sup{top:-0.5em;}sub{bottom:-0.25em;}dl,menu,ol,ul{margin:1em 0;}dd{margin:0 0 0 40px;}menu,ol,ul{padding:0 0 0 40px;}nav ul,nav ol{list-style:none;list-style-image:none;}img{border:0;-ms-interpolation-mode:bicubic;}svg:not(:root){overflow:hidden;}figure{margin:0;}form{margin:0;}fieldset{border:1px solid #c0c0c0;margin:0 2px;padding:0.35em 0.625em 0.75em;}legend{border:0;padding:0;white-space:normal;*margin-left:-7px;}button,input,select,textarea{font-size:100%;margin:0;vertical-align:baseline;*vertical-align:middle;}button,input{line-height:normal;}button,html input[type="button"],input[type="reset"],input[type="submit"]{-webkit-appearance:button;cursor:pointer;*overflow:visible;}button[disabled],input[disabled]{cursor:default;}input[type="checkbox"],input[type="radio"]{box-sizing:border-box;padding:0;*height:13px;*width:13px;}input[type="search"]{-webkit-appearance:textfield;-moz-box-sizing:content-box;-webkit-box-sizing:content-box;box-sizing:content-box;}input[type="search"]::-webkit-search-cancel-button,input[type="search"]::-webkit-search-decoration{-webkit-appearance:none;}button::-moz-focus-inner,input::-moz-focus-inner{border:0;padding:0;}textarea{overflow:auto;vertical-align:top;}table{border-collapse:collapse;border-spacing:0;}
    """

    TEMPLATE_HTML_STYLES = """
    body {
        font-size: 14px;
        Font-family: "Helvetica";
    }
    .clearfix:after {
       content: " "; /* Older browser do not support empty content */
       visibility: hidden;
       display: block;
       height: 0;
       clear: both;
    }
   .error {
        color: #cc0000;
        font-weight: 500;
    }
   .container {
        margin: 0 15px 0;
    }
    @media all and (min-width: 1300px) {
        .container {
            margin: 0 auto 0;
            width: 1200px;
        }
    }
    @media all and (min-width: 1650px) {
        .container {
            margin: 0 auto 0;
            width: 1500px;
        }
    }
    h1 {
        font-weight: 700;
        font-size: 32px;
        color: #333;
        margin: 0;
        padding: 0px 0 30px;
    }
    .header {
        padding: 15px 0 15px;
        border-bottom: 1px solid #eee;
    }
    .footer {
        padding: 15px 0 15px;
        border-top: 1px solid #eee;
    }
    .main {
        padding: 15px 0 15px;
    }
    .wrapper {
        width: 100%; max-width: 100%; overflow-x: auto;
    }
    .mdmreport-banner {
        display: block; position: relative; padding: 1em; margin: 0 0 1em; border: #ddd solid 1px;
    }
"""

    TEMPLATE_HTML_STYLES_TABLE = """
.mdmreport-table, mdmreport-table tbody, .mdmreport-table thead, .mdmreport-table tr, .mdmreport-table td {
    margin: 0;
    padding: 0;
    line-height: 16px;
    border-collapse: collapse; border-spacing: 1px;
    border: 1px #ddd solid;
}

.mdmreport-table .mdmreport-record {
    background: #fff;
}

.mdmreport-table .mdmreport-record:hover {
    background: #e7e7e7;
}

/* all regular cells */ .mdmreport-table .mdmreport-record td {
    padding: 0.25em 0.5em;
    max-width: 15em;
    overflow: hidden;
    overflow-wrap: anywhere;
}
/* first cell with item name */ .mdmreport-table .mdmreport-record td:first-child {
    max-width: 45em;
    overflow: visible;
}
/* 2nd cell with label */ .mdmreport-table .mdmreport-record td:first-child + td {
    max-width: 45em;
}
/* first row */ .mdmreport-table .mdmreport-record:first-child td {
    font-weight: 600;
    padding-top: 0.85em;
    padding-bottom: 0.85em;
}




.mdmreport-table .mdmreport-record {
    position: relative;
}
.mdmreport-table .mdmreport-record.mdmdiff-added {
    background: #c8f0da;
}
/* .mdmreport-table .mdmreport-record.mdmdiff-added td { */
/*     padding-top: 1.2em; */
/* } */
/* .mdmreport-table .mdmreport-record.mdmdiff-added td:first-child:before { */
/*     content: ""added""; */
/*     display: block; */
/*     position: absolute; */
/*     padding-right: 0.5em; */
/*     top: 0; */
/*     padding-top: 0; */
/*     color: #090; */
/*     z-index: 999; */
/*     font-weight: 700; */
/*     font-size: 70%; */
/* } */
.mdmreport-table .mdmreport-record.mdmdiff-removed {
    background: #ffcbbd;
}
/* .mdmreport-table .mdmreport-record.mdmdiff-removed td { */
/*     padding-top: 1.2em; */
/* } */
/* .mdmreport-table .mdmreport-record.mdmdiff-removed td:first-child:before { */
/*     content: ""removed""; */
/*     display: block; */
/*     position: absolute; */
/*     padding-right: 0.5em; */
/*     top: 0; */
/*     padding-top: 0; */
/*     color: #b00; */
/*     z-index: 999; */
/*     font-weight: 700; */
/*     font-size: 70%; */
/* } */
.mdmreport-table .mdmreport-record.mdmdiff-ghost {
    background: #eeeeee;
    color: #444444;
}
.mdmreport-table .mdmreport-record.mdmdiff-diff {
    background: #ffe49c;
}
.mdmdiff-inlineoverlay-added { background: #6bc795; }
.mdmdiff-inlineoverlay-removed { background: #f59278; }
.mdmdiff-inlineoverlay-diff { background: #edbf45; }


/* controls */

.mdmreport-controls fieldset, fieldset.mdmreport-controls, .mdmreport-controls form, form.mdmreport-controls { display: block; border: none; margin: 0; padding: 0; }
.mdmreport-controls legend, .mdmreport-controls label {
    display: inline-block;
    line-height: 1em;
    padding: 0.35em;
    min-height: 1.3em;
}
.mdmreport-controls label {
    border: 1px solid transparent;
    transition: all 350ms ease;
}
.mdmreport-controls label:hover {
    border: 1px solid #ddd;
}
.mdmreport-controls label input[type="checkbox"] {
    display: inline-block;
    width: 0;
    margin-left: 1.35em;
    position: relative;
}
.mdmreport-controls label input[type="checkbox"]:before {
    content: " ";
    display: block;
    text-align: center;
    position: absolute;
    width: 1em;
    height: 1em;
    background: #fff;
    border: 1px solid #ddd;
    right: 100%;
    transform: translateX(-0.35em);
    line-height: .8em;
    padding: 0.1em 0 0.1em;
}
.mdmreport-controls label input[type="checkbox"]:checked:before {
    content: "\\002A09";
}
.mdmreport-controls-group input.mdmreport-controls[type="text"], .mdmreport-controls .mdmreport-controls-group input[type="text"] {
    display: block;
    line-height: 1em;
    padding: 0.35em;
    min-height: 1.3em;
    width: 100%;
    border: 1px solid #dddddd;
    border-radius: 0.18em;
}

.mdmreport-controls[disabled], .mdmreport-controls.disabled {
    position: relative;
}
.mdmreport-controls[disabled]:before, .mdmreport-controls.disabled:before {
    content: " ";
    display: block;
    position: absolute;
    left: 0; top: 0; right: 0; bottom: 0;
    background: rgba(224,224,224,0.55);
}
</style>

    """

    TEMPLATE_HTML_SCRIPTS = """
<script>
(function(){
    function mdmrepInitJSPart(){
        let errorBannerEl = null;
        try {
            errorBannerEl = document.querySelector('#error_banner');
            if( !errorBannerEl ) throw new Error('no error banner, stop execution of js scripts');
        } catch(e) {
            throw e;
            return;
        }
        try {
            /* columns, rows ... */
            const tablesEl = document.querySelectorAll('table.mdmreport-table');
            const pluginHolderEl = document.querySelector('#mdmreport_plugin_placeholder');
            Array.prototype.forEach.call(tablesEl,function(tableEl){
                document.dispatchEvent( new CustomEvent('mdmreport-oninit',{detail:{tableEl:tableEl,errorBannerEl:errorBannerEl,pluginHolderEl:pluginHolderEl}}) );
                const headerRowsEl = tableEl.querySelectorAll('tr:is(:first-child)');
                if(!(headerRowsEl.length>0)) { (()=>{ try { errorBannerEl.innerHTML = errorBannerEl.innerHTML + `Warning: css col and row classes: no first row<br />`; } catch(ee) {}; throw new Error('Warning: css col and row classes: no first row'); })(); return; };
                Array.prototype.forEach.call(headerRowsEl,function(rowEl) {
                    Array.prototype.forEach.call(rowEl.querySelectorAll('td'),function(colEl){
                        document.dispatchEvent( new CustomEvent('mdmreport-onheadercol',{detail:{colEl:colEl,tableEl:tableEl,errorBannerEl:errorBannerEl,pluginHolderEl:pluginHolderEl}}) );
                    });
                });
                const rowsEl = tableEl.querySelectorAll('tr:not(:first-child)');
                Array.prototype.forEach.call(rowsEl,function(rowEl){
                    const colsEl = rowEl.querySelectorAll('td');
                    document.dispatchEvent( new CustomEvent('mdmreport-onrow',{detail:{rowEl:rowEl,colsEl:colsEl,tableEl:tableEl,errorBannerEl:errorBannerEl,pluginHolderEl:pluginHolderEl}}) );
                });
                document.dispatchEvent( new CustomEvent('mdmreport-onfinishedrowevents',{detail:{tableEl:tableEl,errorBannerEl:errorBannerEl,pluginHolderEl:pluginHolderEl}}) );
            });
            document.removeEventListener('DOMContentLoaded',mdmrepInitJSPart);
        } catch(e) {
            try {
                errorBannerEl.innerHTML = errorBannerEl.innerHTML + `Error: ${e}<br />`;
            } catch(ee) {};
            try {
                document.removeEventListener('DOMContentLoaded',mdmrepInitJSPart);
            } catch(ee) {}
            throw e;
        }
    }
    window.mdmrepInitJSPart = mdmrepInitJSPart;
    document.addEventListener('DOMContentLoaded',mdmrepInitJSPart);
})();
</script>
<style>
    /* === show/hide columns css === */
.mdmreport-hidecol-col-0 .mdmreport-cols-col-0, .mdmreport-hidecol-col-1 .mdmreport-cols-col-1, .mdmreport-hidecol-col-2 .mdmreport-cols-col-2, .mdmreport-hidecol-col-3 .mdmreport-cols-col-3, .mdmreport-hidecol-col-4 .mdmreport-cols-col-4, .mdmreport-hidecol-col-5 .mdmreport-cols-col-5, .mdmreport-hidecol-col-6 .mdmreport-cols-col-6, .mdmreport-hidecol-col-7 .mdmreport-cols-col-7, .mdmreport-hidecol-col-8 .mdmreport-cols-col-8, .mdmreport-hidecol-col-9 .mdmreport-cols-col-9, .mdmreport-hidecol-col-10 .mdmreport-cols-col-10, .mdmreport-hidecol-col-11 .mdmreport-cols-col-11, .mdmreport-hidecol-col-12 .mdmreport-cols-col-12, .mdmreport-hidecol-col-13 .mdmreport-cols-col-13, .mdmreport-hidecol-col-14 .mdmreport-cols-col-14, .mdmreport-hidecol-col-15 .mdmreport-cols-col-15, .mdmreport-hidecol-col-16 .mdmreport-cols-col-16, .mdmreport-hidecol-col-17 .mdmreport-cols-col-17, .mdmreport-hidecol-col-18 .mdmreport-cols-col-18, .mdmreport-hidecol-col-19 .mdmreport-cols-col-19, .mdmreport-hidecol-col-20 .mdmreport-cols-col-20, .mdmreport-hidecol-col-21 .mdmreport-cols-col-21, .mdmreport-hidecol-col-22 .mdmreport-cols-col-22, .mdmreport-hidecol-col-23 .mdmreport-cols-col-23, .mdmreport-hidecol-col-24 .mdmreport-cols-col-24, .mdmreport-hidecol-col-25 .mdmreport-cols-col-25, .mdmreport-hidecol-col-26 .mdmreport-cols-col-26, .mdmreport-hidecol-col-27 .mdmreport-cols-col-27, .mdmreport-hidecol-col-28 .mdmreport-cols-col-28, .mdmreport-hidecol-col-29 .mdmreport-cols-col-29, .mdmreport-hidecol-col-30 .mdmreport-cols-col-30, .mdmreport-hidecol-col-31 .mdmreport-cols-col-31, .mdmreport-hidecol-col-32 .mdmreport-cols-col-32, .mdmreport-hidecol-col-33 .mdmreport-cols-col-33, .mdmreport-hidecol-col-34 .mdmreport-cols-col-34, .mdmreport-hidecol-col-35 .mdmreport-cols-col-35, .mdmreport-hidecol-col-36 .mdmreport-cols-col-36, .mdmreport-hidecol-col-37 .mdmreport-cols-col-37, .mdmreport-hidecol-col-38 .mdmreport-cols-col-38, .mdmreport-hidecol-col-39 .mdmreport-cols-col-39, .mdmreport-hidecol-col-40 .mdmreport-cols-col-40, .mdmreport-hidecol-col-41 .mdmreport-cols-col-41, .mdmreport-hidecol-col-42 .mdmreport-cols-col-42, .mdmreport-hidecol-col-43 .mdmreport-cols-col-43, .mdmreport-hidecol-col-44 .mdmreport-cols-col-44, .mdmreport-hidecol-col-45 .mdmreport-cols-col-45, .mdmreport-hidecol-col-46 .mdmreport-cols-col-46, .mdmreport-hidecol-col-47 .mdmreport-cols-col-47, .mdmreport-hidecol-col-48 .mdmreport-cols-col-48, .mdmreport-hidecol-col-49 .mdmreport-cols-col-49, .mdmreport-hidecol-col-50 .mdmreport-cols-col-50, .mdmreport-hidecol-col-51 .mdmreport-cols-col-51, .mdmreport-hidecol-col-52 .mdmreport-cols-col-52, .mdmreport-hidecol-col-53 .mdmreport-cols-col-53, .mdmreport-hidecol-col-54 .mdmreport-cols-col-54, .mdmreport-hidecol-col-55 .mdmreport-cols-col-55, .mdmreport-hidecol-col-56 .mdmreport-cols-col-56, .mdmreport-hidecol-col-57 .mdmreport-cols-col-57, .mdmreport-hidecol-col-58 .mdmreport-cols-col-58, .mdmreport-hidecol-col-59 .mdmreport-cols-col-59, .mdmreport-hidecol-col-60 .mdmreport-cols-col-60, .mdmreport-hidecol-col-61 .mdmreport-cols-col-61, .mdmreport-hidecol-col-62 .mdmreport-cols-col-62, .mdmreport-hidecol-col-63 .mdmreport-cols-col-63, .mdmreport-hidecol-col-64 .mdmreport-cols-col-64, .mdmreport-hidecol-col-65 .mdmreport-cols-col-65, .mdmreport-hidecol-col-66 .mdmreport-cols-col-66, .mdmreport-hidecol-col-67 .mdmreport-cols-col-67, .mdmreport-hidecol-col-68 .mdmreport-cols-col-68, .mdmreport-hidecol-col-69 .mdmreport-cols-col-69, .mdmreport-hidecol-col-70 .mdmreport-cols-col-70, .mdmreport-hidecol-col-71 .mdmreport-cols-col-71, .mdmreport-hidecol-col-72 .mdmreport-cols-col-72, .mdmreport-hidecol-col-73 .mdmreport-cols-col-73, .mdmreport-hidecol-col-74 .mdmreport-cols-col-74, .mdmreport-hidecol-col-75 .mdmreport-cols-col-75, .mdmreport-hidecol-col-76 .mdmreport-cols-col-76, .mdmreport-hidecol-col-77 .mdmreport-cols-col-77, .mdmreport-hidecol-col-78 .mdmreport-cols-col-78, .mdmreport-hidecol-col-79 .mdmreport-cols-col-79, .mdmreport-hidecol-col-80 .mdmreport-cols-col-80, .mdmreport-hidecol-col-81 .mdmreport-cols-col-81, .mdmreport-hidecol-col-82 .mdmreport-cols-col-82, .mdmreport-hidecol-col-83 .mdmreport-cols-col-83, .mdmreport-hidecol-col-84 .mdmreport-cols-col-84, .mdmreport-hidecol-col-85 .mdmreport-cols-col-85, .mdmreport-hidecol-col-86 .mdmreport-cols-col-86, .mdmreport-hidecol-col-87 .mdmreport-cols-col-87, .mdmreport-hidecol-col-88 .mdmreport-cols-col-88, .mdmreport-hidecol-col-89 .mdmreport-cols-col-89, .mdmreport-hidecol-col-90 .mdmreport-cols-col-90, .mdmreport-hidecol-col-91 .mdmreport-cols-col-91, .mdmreport-hidecol-col-92 .mdmreport-cols-col-92, .mdmreport-hidecol-col-93 .mdmreport-cols-col-93, .mdmreport-hidecol-col-94 .mdmreport-cols-col-94, .mdmreport-hidecol-col-95 .mdmreport-cols-col-95, .mdmreport-hidecol-col-96 .mdmreport-cols-col-96, .mdmreport-hidecol-col-97 .mdmreport-cols-col-97, .mdmreport-hidecol-col-98 .mdmreport-cols-col-98, .mdmreport-hidecol-col-99 .mdmreport-cols-col-99, .mdmreport-hidecol-col-100 .mdmreport-cols-col-100 { display: none; }
    /* === end of show/hide columns css === */
</style>
<script>
(function() {
    /* === show/hide columns js === */
    const headerCols = [];
    const getElText = function(el) { return el.innerText||el.textContent };
    let bannerCreatedPromiseResolve = () => { throw new Error('please init the promise object first'); };
    let bannerCreatedPromiseReject = () => { throw new Error('please init the promise object first'); };
    const bannerCreatedPromise = new Promise((resolve,reject)=>{ bannerCreatedPromiseResolve = resolve; bannerCreatedPromiseReject = reject; });
    function init(event) {
        let errorBannerEl;
        try {
            errorBannerEl = event.detail.errorBannerEl;
        } catch(e) {
            throw e;
        }
        try {
            const pluginHolderEl = event.detail.pluginHolderEl;
            const bannerEl = document.createElement('div');
            bannerEl.className = 'mdmreport-layout-plugin mdmreport-banner mdmreport-banner-columns';
            bannerEl.innerHTML = '<form method="_POST" action="#!" onSubmit="javascript: return false;" class="mdmreport-controls"><fieldset class="mdmreport-controls"><div><legend>Show/hide columns:</legend></div></fieldset></form>';
            Array.prototype.forEach.call(bannerEl.querySelectorAll('form'),function(formEl){formEl.addEventListener('submit',function(event){event.preventDefault();event.stopPropagation();return false;});});
            pluginHolderEl.append(bannerEl);
            bannerCreatedPromiseResolve(bannerEl);
            try {
                document.removeEventListener('mdmreport-oninit',init);
            } catch(ee) {}
        } catch(e) {
            try {
                errorBannerEl.innerHTML = errorBannerEl.innerHTML + `Error: ${e}<br />`;
            } catch(ee) {};
            try {
                document.removeEventListener('mdmreport-oninit',init);
            } catch(ee) {}
            throw e;
        }
    }
    document.addEventListener('mdmreport-oninit',init);
    function processOnCol(event){
        let errorBannerEl;
        try {
            errorBannerEl = event.detail.errorBannerEl;
        } catch(e) {
            throw e;
        }
        try {
            const colEl = event.detail.colEl;
            const tableEl = event.detail.tableEl;
            const colClassName = `col-${headerCols.length}`;
            colEl.classList.add(`mdmreport-cols-${colClassName}`);
            const colText = getElText(colEl);
            headerCols.push( colText );
            bannerCreatedPromise.then(function(bannerEl) {
                try {
                    const labelEl = document.createElement('label');
                    labelEl.textContent = colText;
                    labelEl.classList.add('mdmreport-controls');
                    const checkboxEl = document.createElement('input');
                    checkboxEl.setAttribute('type','checkbox');
                    checkboxEl.setAttribute('checked','true');
                    checkboxEl.checked = true;
                    checkboxEl.addEventListener('change',function(event){
                        const checkboxEl = event.target;
                        const className = `mdmreport-hidecol-${colClassName}`;
                        if( checkboxEl.checked ) {
                            tableEl.classList.remove(className);
                        } else {
                            tableEl.classList.add(className);
                        };
                    });
                    labelEl.prepend(checkboxEl);
                    bannerEl.querySelector('fieldset').append(labelEl);
                } catch(e) {
                    try {
                        errorBannerEl.innerHTML = errorBannerEl.innerHTML + `Error: ${e}<br />`;
                    } catch(ee) {};
                    throw e;
                }
            });
        } catch(e) {
            try {
                errorBannerEl.innerHTML = errorBannerEl.innerHTML + `Error: ${e}<br />`;
            } catch(ee) {};
            throw e;
        }
    }
    document.addEventListener('mdmreport-onheadercol',processOnCol);
    function processOnRow(event){
        let errorBannerEl;
        try {
            errorBannerEl = event.detail.errorBannerEl;
        } catch(e) {
            throw e;
        }
        try {
            const rowEl = event.detail.rowEl;
            const colsEl = event.detail.colsEl;
            if(!(colsEl.length>0)) { (()=>{ try { errorBannerEl.innerHTML = errorBannerEl.innerHTML + `Warning: css classes: no first col<br />`; } catch(ee) {}; throw new Error('Warning: no first col'); })(); return; };
            Array.prototype.forEach.call(colsEl,function(colEl,i){
                const colClassName = `col-${i}`;
                colEl.classList.add(`mdmreport-cols-${colClassName}`);
            });
        } catch(e) {
            try {
                errorBannerEl.innerHTML = errorBannerEl.innerHTML + `Error: ${e}<br />`;
            } catch(ee) {};
            throw e;
        }
    }
    document.addEventListener('mdmreport-onrow',processOnRow);
    function cleanHandlers() {
        try {
            document.removeEventListener('mdmreport-onheadercol',processOnCol);
        } catch(ee) {}
        try {
            document.removeEventListener('mdmreport-onrow',processOnRow);
        } catch(ee) {}
        try {
            document.removeEventListener('mdmreport-onfinishedrowevents',cleanHandlers);
        } catch(ee) {}
    }
    document.addEventListener('mdmreport-onfinishedrowevents',cleanHandlers);
})();
    /* === end of show/hide columns js === */
</script>
    """

    TEMPLATE_HTML_FIELDSREPORT_SCRIPTS = """
<script>
/* TBD, maybe I'll add something */
</script>
    """

    TEMPLATE_HTML_JSONDIFF_SCRIPTS = """
<script>
    /* === add diff classes to rows based on the first cell contents in each row, it contains "diff"/"added"/"removed"/"(info)" texts, js === */
(function() {
    function process(event){
        let errorBannerEl;
        try {
            errorBannerEl = event.detail.errorBannerEl;
        } catch(e) {
            throw e;
        }
        try {
            const rowEl = event.detail.rowEl;
            const colsEl = event.detail.colsEl;
            if(!(colsEl.length>0)) { (()=>{ try { errorBannerEl.innerHTML = errorBannerEl.innerHTML + `Warning: css diff classes: no first col<br />`; } catch(ee) {}; throw new Error('Warning: no first col'); })(); return; };
            const colFirstEl = [colsEl[0]];
            const diffflag =  colFirstEl[0].innerText||colFirstEl[0].textContent;
            if( /^\\s*?added\\s*?$/.test(diffflag) )
                rowEl.classList.add('mdmdiff-added');
            else if( /^\\s*?removed\\s*?$/.test(diffflag) )
                rowEl.classList.add('mdmdiff-removed');
            else if( /^\\s*?diff\\s*?$/.test(diffflag) )
                rowEl.classList.add('mdmdiff-diff');
            else if( /^\\s*?\\(\\s*?moved\\s*?\\)\\s*?$/.test(diffflag) )
                rowEl.classList.add('mdmdiff-ghost');
            else if( /^\\s*?\\(\\s*?info\\s*?\\)\\s*?$/.test(diffflag) )
                rowEl.classList.add('mdmdiff-ghost');
        } catch(e) {
            try {
                errorBannerEl.innerHTML = errorBannerEl.innerHTML + `Error: ${e}<br />`;
            } catch(ee) {};
            throw e;
        }
    }
    document.addEventListener('mdmreport-onrow',process);
    function cleanHandlers() {
        try {
            document.removeEventListener('mdmreport-onrow',process);
        } catch(ee) {}
        try {
            document.removeEventListener('mdmreport-onfinishedrowevents',cleanHandlers);
        } catch(ee) {}
    }
    document.addEventListener('mdmreport-onfinishedrowevents',cleanHandlers);
})();
    /* === end of add diff classes to rows based on the first cell contents in each row, it contains "diff"/"added"/"removed"/"(info)" texts, js === */
</script>
<style>
    /* === show/hide rows css === */
.mdmreport-hiderowsutil-showselectedonlymode .mdmreport-record {
    display: none;
}
.mdmreport-hiderowsutil-showselectedonlymode .mdmreport-record:first-child {
    display: table-row;
}
.mdmreport-hiderowsutil-showselectedonlymode.mdmreport-hiderowsutil-show-diffcols-col-2 .mdmreport-record.mdmreport-diffincols-col-2
, .mdmreport-hiderowsutil-showselectedonlymode.mdmreport-hiderowsutil-show-diffcols-col-3 .mdmreport-record.mdmreport-diffincols-col-3
, .mdmreport-hiderowsutil-showselectedonlymode.mdmreport-hiderowsutil-show-diffcols-col-4 .mdmreport-record.mdmreport-diffincols-col-4
, .mdmreport-hiderowsutil-showselectedonlymode.mdmreport-hiderowsutil-show-diffcols-col-5 .mdmreport-record.mdmreport-diffincols-col-5
, .mdmreport-hiderowsutil-showselectedonlymode.mdmreport-hiderowsutil-show-diffcols-col-6 .mdmreport-record.mdmreport-diffincols-col-6
, .mdmreport-hiderowsutil-showselectedonlymode.mdmreport-hiderowsutil-show-diffcols-col-7 .mdmreport-record.mdmreport-diffincols-col-7 {
    display: table-row;
}
    /* === end of show/hide rows css === */
</style>
<script>
(function() {
    /* === show/hide rows js === */
    const headerCols = [];
    const headerUniqueCols = [];
    const getElText = function(el) { return el.innerText||el.textContent };
    let bannerCreatedPromiseResolve = () => { throw new Error('please init the promise object first'); };
    let bannerCreatedPromiseReject = () => { throw new Error('please init the promise object first'); };
    const bannerCreatedPromise = new Promise((resolve,reject)=>{ bannerCreatedPromiseResolve = resolve; bannerCreatedPromiseReject = reject; });
    function init(event) {
        let errorBannerEl;
        try {
            errorBannerEl = event.detail.errorBannerEl;
        } catch(e) {
            throw e;
        }
        try {
            const pluginHolderEl = event.detail.pluginHolderEl;
            const tableEl = event.detail.tableEl;
            const bannerEl = document.createElement('div');
            bannerEl.className = 'mdmreport-layout-plugin mdmreport-banner mdmreport-banner-rows';
            bannerEl.innerHTML = '<form method="_POST" action="#!" onSubmit="javascript: return false;" class="mdmreport-controls"><fieldset class="mdmreport-controls"><div><legend>Show/hide rows with diffs in these columns only:</legend></div></fieldset></form>';
            Array.prototype.forEach.call(bannerEl.querySelectorAll('form'),function(formEl){formEl.addEventListener('submit',function(event){event.preventDefault();event.stopPropagation();return false;});});
            pluginHolderEl.append(bannerEl);
            (function(bannerEl){
                const labelEl = document.createElement('label');
                labelEl.textContent = 'Show all';
                labelEl.classList.add('mdmreport-controls');
                labelEl.classList.add('mdmreport-plugn-rows-control');
                labelEl.classList.add('mdmreport-plugn-rows-control-showall');
                const checkboxEl = document.createElement('input');
                checkboxEl.setAttribute('type','checkbox');
                checkboxEl.setAttribute('checked','true');
                checkboxEl.checked = true;
                const handleShowAllChange = function(event){
                    const checkboxEl = event.target;
                    const className = `mdmreport-hiderowsutil-showselectedonlymode`;
                    if( !checkboxEl.checked ) {
                        tableEl.classList.add(className);
                        Array.prototype.forEach.call(bannerEl.querySelectorAll('.mdmreport-plugn-rows-control-customcolumnfilter'),function(labelEl) { labelEl.classList.remove('disabled'); Array.prototype.forEach.call(labelEl.querySelectorAll('input'),function(inputEl){inputEl.removeAttribute('disabled');}); });
                    } else {
                        tableEl.classList.remove(className);
                        Array.prototype.forEach.call(bannerEl.querySelectorAll('.mdmreport-plugn-rows-control-customcolumnfilter'),function(labelEl) { labelEl.classList.add('disabled'); Array.prototype.forEach.call(labelEl.querySelectorAll('input'),function(inputEl){inputEl.setAttribute('disabled','true');}); });
                    };
                };
                checkboxEl.addEventListener('change',handleShowAllChange);
                setTimeout(()=>{handleShowAllChange({target:checkboxEl});},100);
                labelEl.prepend(checkboxEl);
                bannerEl.querySelector('fieldset').append(labelEl);
            })(bannerEl);
            bannerCreatedPromiseResolve(bannerEl);
            try {
                document.removeEventListener('mdmreport-oninit',init);
            } catch(ee) {}
        } catch(e) {
            try {
                errorBannerEl.innerHTML = errorBannerEl.innerHTML + `Error: ${e}<br />`;
            } catch(ee) {};
            try {
                document.removeEventListener('mdmreport-oninit',init);
            } catch(ee) {}
            throw e;
        }
    }
    document.addEventListener('mdmreport-oninit',init);
    function processHeaderCol(event) {
        let errorBannerEl;
        try {
            errorBannerEl = event.detail.errorBannerEl;
        } catch(e) {
            throw e;
        }
        try {
            const colEl = event.detail.colEl;
            const tableEl = event.detail.tableEl;
            const colNum = headerCols.length;
            let isUnique = undefined;
            const colClassName = `col-${colNum}`;
            const colText = getElText(colEl);
            headerCols.push( colText );
            if( colNum<2 )
                return;
            const colTextClean = colText.replace(/^(?:(?:&#32;)|(?:\\s))*?(?:(?:&#40;)|(?:\\())(?:(?:&#32;)|(?:\\s))*?\\w+(?:(?:&#32;)|(?:\\s))MDD(?:(?:&#32;)|(?:\\s))*?(?:(?:&#41;)|(?:\\)))(?:(?:&#32;)|(?:\\s))*/,'').replace(/(?:(?:&#32;)|(?:\\s))*$/,'');
            if(headerUniqueCols.map(e=>e.textClean).includes(colTextClean)) {
                headerUniqueCols[headerUniqueCols.map(e=>e.textClean).indexOf(colTextClean)].colIndices.push(colNum);
                isUnique = false;
            } else {
                headerUniqueCols.push({textClean:colTextClean,colIndices:[colNum]});
                isUnique = true;
            }
            const createCheckboxControl = !isUnique ? () => undefined : function(bannerEl) {
                const labelEl = document.createElement('label');
                labelEl.textContent = colTextClean;
                labelEl.classList.add('mdmreport-controls');
                labelEl.classList.add('mdmreport-plugn-rows-control');
                labelEl.classList.add('mdmreport-plugn-rows-control-customcolumnfilter');
                const checkboxEl = document.createElement('input');
                checkboxEl.setAttribute('type','checkbox');
                checkboxEl.setAttribute('checked','true');
                checkboxEl.checked = true;
                const colIndices = headerUniqueCols[headerUniqueCols.map(e=>e.textClean).indexOf(colTextClean)].colIndices;
                const changeHandler = function(event) {
                    const checkboxEl = event.target;
                    const classNames = colIndices.map(n=>`mdmreport-hiderowsutil-show-diffcols-col-${n}`);
                    if( checkboxEl.checked ) {
                        tableEl.classList.add(...classNames);
                    } else {
                        tableEl.classList.remove(...classNames);
                    };
                };
                changeHandler({target:checkboxEl});
                checkboxEl.addEventListener('change',changeHandler);
                labelEl.prepend(checkboxEl);
                bannerEl.querySelector('fieldset').append(labelEl);
            };
            bannerCreatedPromise.then(createCheckboxControl);
        } catch(e) {
            try {
                errorBannerEl.innerHTML = errorBannerEl.innerHTML + `Error: ${e}<br />`;
            } catch(ee) {};
            throw e;
        }
    }
    document.addEventListener('mdmreport-onheadercol',processHeaderCol);
    function processRow(event){
        let errorBannerEl;
        try {
            errorBannerEl = event.detail.errorBannerEl;
        } catch(e) {
            throw e;
        }
        try {
            const rowEl = event.detail.rowEl;
            const colsEl = event.detail.colsEl;
            if(!(colsEl.length>0)) { (()=>{ try { errorBannerEl.innerHTML = errorBannerEl.innerHTML + `Warning: css classes: no first col<br />`; } catch(ee) {}; throw new Error('Warning: no first col'); })(); return; };
            Array.prototype.forEach.call(colsEl,function(colEl,i) {
                let didChange = undefined;
                if( i<2 ) {
                    didChange = false;
                } else if( rowEl.classList.contains('mdmdiff-added') || rowEl.classList.contains('mdmdiff-removed') ) {
                    const colText = getElText(colEl);
                    if( colText!=='' ) {
                        didChange = true;
                    } else {
                        const cleanColumnHeaderText = headerCols[i].replace(/^(?:(?:&#32;)|(?:\\s))*?(?:(?:&#40;)|(?:\\())(?:(?:&#32;)|(?:\\s))*?\\w+(?:(?:&#32;)|(?:\\s))MDD(?:(?:&#32;)|(?:\\s))*?(?:(?:&#41;)|(?:\\)))(?:(?:&#32;)|(?:\\s))*/,'').replace(/(?:(?:&#32;)|(?:\\s))*$/,'');
                        const isALabelColumn = /^(?:(?:&#32;)|(?:\\s))*?Label(?:(?:&#32;)|(?:\\s))*?(?:(?:&#40;)|(?:\\())*?.*?(?:(?:&#42;)|(?:\\)))*?(?:(?:&#32;)|(?:\\s))*?$/.test(cleanColumnHeaderText);
                        if( isALabelColumn ) {
                            didChange = true;
                        } else {
                            didChange = false;
                        }
                    }
                } else if( colEl.querySelectorAll('.mdmdiff-inlineoverlay-added, .mdmdiff-inlineoverlay-removed, .mdmdiff-inlineoverlay-diff').length>0 ) {
                    didChange = true;
                } else {
                    didChange = false;
                }
                if( didChange ) {
                    const colClassName = `col-${i}`;
                    rowEl.classList.add(`mdmreport-diffincols-${colClassName}`);
                }
            });
        } catch(e) {
            try {
                errorBannerEl.innerHTML = errorBannerEl.innerHTML + `Error: ${e}<br />`;
            } catch(ee) {};
            throw e;
        }
    }
    document.addEventListener('mdmreport-onrow',processRow);
    function cleanHandlers() {
        try {
            document.removeEventListener('mdmreport-onheadercol',processHeaderCol);
        } catch(ee) {}
        try {
            document.removeEventListener('mdmreport-onrow',processRow);
        } catch(ee) {}
        try {
            document.removeEventListener('mdmreport-onfinishedrowevents',cleanHandlers);
        } catch(ee) {}
    }
    document.addEventListener('mdmreport-onfinishedrowevents',cleanHandlers);
})();
    /* === end of show/hide rows js === */
</script>
<style>
    /* === statistics css === */
.mdmreport-banner-statistics p {
    font-size: 85%;
    color: #444444;
    line-height: 1em;
    margin: 0.6em 0 0;
    padding: 0;
}
    /* === end of statistics css === */
</style>
<script>
(function() {
    /* === statistics js === */
    let bannerCreatedPromiseResolve = () => { throw new Error('please init the promise object first'); };
    let bannerCreatedPromiseReject = () => { throw new Error('please init the promise object first'); };
    const bannerCreatedPromise = new Promise((resolve,reject)=>{ bannerCreatedPromiseResolve = resolve; bannerCreatedPromiseReject = reject; });
    const rowsCalculateStatistics = {
        'total': [],
        'added': [],
        'removed': [],
        'info': [],
        'ghostmoved': [],
        'left': [],
        'right': []
    };
    let lastRowNumber = 0;
    function init(event) {
        let errorBannerEl;
        try {
            errorBannerEl = event.detail.errorBannerEl;
        } catch(e) {
            throw e;
        }
        try {
            const pluginHolderEl = event.detail.pluginHolderEl;
            const tableEl = event.detail.tableEl;
            const bannerEl = document.createElement('div');
            bannerEl.className = 'mdmreport-layout-plugin mdmreport-banner mdmreport-banner-statistics';
            bannerEl.innerHTML = '<legend>Statistics</legend>';
            pluginHolderEl.append(bannerEl);

            const pTotalEl = document.createElement('p');
            pTotalEl.textContent = 'Total rows in the report: ';
            spanTotalCountEl = document.createElement('span');
            spanTotalCountEl.textContent = '???';
            pTotalEl.append(spanTotalCountEl);
            const pAddedEl = document.createElement('p');
            pAddedEl.textContent = 'Added rows: ';
            spanAddedCountEl = document.createElement('span');
            spanAddedCountEl.textContent = '???';
            pAddedEl.append(spanAddedCountEl);
            const pRemovedEl = document.createElement('p');
            pRemovedEl.textContent = 'Removed rows: ';
            spanRemovedCountEl = document.createElement('span');
            spanRemovedCountEl.textContent = '???';
            pRemovedEl.append(spanRemovedCountEl);
            const pLeftEl = document.createElement('p');
            pLeftEl.textContent = 'So that in the report for the left MDD it would be: ';
            spanLeftCountEl = document.createElement('span');
            spanLeftCountEl.textContent = '???';
            pLeftEl.append(spanLeftCountEl);
            const pRightEl = document.createElement('p');
            pRightEl.textContent = 'in right MDD: ';
            spanRightCountEl = document.createElement('span');
            spanRightCountEl.textContent = '???';
            pRightEl.append(spanRightCountEl);

            bannerEl.append(pTotalEl);
            bannerEl.append(pAddedEl);
            bannerEl.append(pRemovedEl);
            bannerEl.append(pLeftEl);
            bannerEl.append(pRightEl);

            bannerCreatedPromiseResolve({spanTotalCountEl,spanAddedCountEl,spanRemovedCountEl,spanLeftCountEl,spanRightCountEl});
            try {
                document.removeEventListener('mdmreport-oninit',init);
            } catch(ee) {}
        } catch(e) {
            try {
                errorBannerEl.innerHTML = errorBannerEl.innerHTML + `Error: ${e}<br />`;
            } catch(ee) {};
            try {
                document.removeEventListener('mdmreport-oninit',init);
            } catch(ee) {}
            throw e;
        }
    }
    document.addEventListener('mdmreport-oninit',init);
    function processRow(event){
        let errorBannerEl;
        try {
            errorBannerEl = event.detail.errorBannerEl;
        } catch(e) {
            throw e;
        }
        try {
            const rowIndex = lastRowNumber;
            lastRowNumber++;
            const rowEl = event.detail.rowEl;
            const colsEl = event.detail.colsEl;
            if(!(colsEl.length>0)) { (()=>{ try { errorBannerEl.innerHTML = errorBannerEl.innerHTML + `Warning: css diff classes: no first col<br />`; } catch(ee) {}; throw new Error('Warning: no first col'); })(); return; };
            const colFirstEl = [colsEl[0]];
            const diffflag =  colFirstEl[0].innerText||colFirstEl[0].textContent;
            let isAdded, isRemoved, isInfo, isGhostMoved;
            if( /^\\s*?added\\s*?$/.test(diffflag) )
                isAdded = true;
            else
                isAdded = false;
            if( /^\\s*?removed\\s*?$/.test(diffflag) )
                isRemoved = true;
            else
                isRemoved = false;
            if( /^\\s*?\(\\s*?info\\s*?\\)\\s*?$/.test(diffflag) )
                isInfo = true;
            else
                isInfo = false;
            if( /^\\s*?\\(\\s*?moved\\s*?\\)\\s*?$/.test(diffflag) )
                isGhostMoved = true;
            else
                isGhostMoved = false;
            rowsCalculateStatistics.total.push(rowIndex);
            if( isAdded )
                rowsCalculateStatistics.added.push(rowIndex);
            if( isRemoved )
                rowsCalculateStatistics.removed.push(rowIndex);
            if( isInfo )
                rowsCalculateStatistics.info.push(rowIndex);
            if( isGhostMoved )
                rowsCalculateStatistics.ghostmoved.push(rowIndex);
            if( !isAdded && !isGhostMoved )
                rowsCalculateStatistics.left.push(rowIndex);
            if( !isRemoved && !isGhostMoved )
                rowsCalculateStatistics.right.push(rowIndex);
        } catch(e) {
            try {
                errorBannerEl.innerHTML = errorBannerEl.innerHTML + `Error: ${e}<br />`;
            } catch(ee) {};
            throw e;
        }
    }
    document.addEventListener('mdmreport-onrow',processRow);
    function finishUp(event) {
        let errorBannerEl;
        try {
            errorBannerEl = event.detail.errorBannerEl;
        } catch(e) {
            throw e;
        }
        bannerCreatedPromise.then(function({spanTotalCountEl,spanAddedCountEl,spanRemovedCountEl,spanLeftCountEl,spanRightCountEl}) {
            try {
                spanTotalCountEl.textContent = `${rowsCalculateStatistics.total.length}`;
                spanAddedCountEl.textContent = `${rowsCalculateStatistics.added.length}`;
                spanRemovedCountEl.textContent = `${rowsCalculateStatistics.removed.length}`;
                spanLeftCountEl.textContent = `${rowsCalculateStatistics.left.length}`;
                spanRightCountEl.textContent = `${rowsCalculateStatistics.right.length}`;
            } catch(e) {
                try {
                    errorBannerEl.innerHTML = errorBannerEl.innerHTML + `Error: ${e}<br />`;
                } catch(ee) {};
                throw e;
            }
        });
    }
    document.addEventListener('mdmreport-onfinishedrowevents',finishUp);
    function cleanHandlers() {
        try {
            document.removeEventListener('mdmreport-onrow',processRow);
        } catch(ee) {}
        try {
            document.removeEventListener('mdmreport-onfinishedrowevents',finishUp);
        } catch(ee) {}
        try {
            document.removeEventListener('mdmreport-onfinishedrowevents',cleanHandlers);
        } catch(ee) {}
    }
    document.addEventListener('mdmreport-onfinishedrowevents',cleanHandlers);
})();
    /* === end of statistics js === */
</script>
<style>
    /* === jira connection css === */
.mdmrep-diff-jiraaddon-col a  {
    display: block;
    max-width: 100%;
    text-overflow: ellipsis;
    overflow: hidden;
    line-height: 1.1em;
    white-space: nowrap;
}
    /* === end of jira connection css === */
</style>
<script>
    /* === jira connection js === */
(function() {
    const validDomains = ['lrwjira.atlassian.net','www.lrwjira.atlassian.net','www.materialplus.atlassian.net','materialplus.atlassian.net'];
    let bannerHolderPromiseResolve = () => { throw new Error('please init the promise first'); };
    let bannerHolderPromiseReject = () => { throw new Error('please init the promise first'); };
    const bannerHolderPromise = new Promise((resolve,reject)=>{ bannerHolderPromiseResolve = resolve; bannerHolderPromiseReject = reject; });
    let runPromiseResolve = () => { throw new Error('please init the promise first'); };
    let runPromiseReject = () => { throw new Error('please init the promise first'); };
    const runPromise = new Promise((resolve,reject)=>{ runPromiseResolve = resolve; runPromiseReject = reject; });
    // itemNameLookup(sanitizeCellText(
    function sanitizeCellText(s) {
        return s.replace(/&\\#(\\d+);/i,function(n,n1){if(isFinite(+n1)) return String.fromCharCode(+n1);else return n;});
    }
    function parsePropertiesText(s) {
        const results = [];
        if( /^\\s*?$/.test(s) )
            return results;
        const matches = s.match( /^\\s*?,?\\s*?(\\w+)\\s*?=\\s*?"((?:(?:[^"])|(?:""))*?)"((?:\\s*?,\\s*?\\w+\\s*?=\\s*?"(?:(?:[^"])|(?:""))*?")*?)\\s*?$/ );
        if( !!matches ) {
            results.push({name:matches[1],value:matches[2].replace(/""/ig,'"')});
            if( !!matches[3] ) {
                results.push(...parsePropertiesText(matches[3]));
            }
            return results;
        } else {
            throw new Error(`can't parse properties at [${s}]`);
        }
    }
    function itemNameLookup(itemName,propertiesData) {
        const extractProperties = () => {};
        if( /^\\s*?Info\\s*?\\:/.test(itemName) ) {
            // info item - skip
            return null;
        } else if( /^\\s*?Types\\.\\w+/.test(itemName) ) {
            // is a shared list
            return itemName.replace(/^\\s*?Types\\.(\\w+)\\b.*?$/ig,'$1').replace(/^\s*?SL_/ig,'');
        } else if( /^\\s*?Fields\\./.test(itemName) ) {
            // "fields" (normal questions) - let's look up the FullName property
            const properties = propertiesData[itemName];
            const propertyListLcase = properties.map(a=>a.name.toLowerCase());
            if( /^\\s*?Fields\\.QCData\.Flags\\b/.test(itemName) ) {
                // A QC Flag - let's look up the "AppliesTo" property
                if( propertyListLcase.includes('AppliesTo'.toLowerCase()) ) {
                    // TODO: best match. or all matches?
                    const appliesto = properties[propertyListLcase.indexOf('AppliesTo'.toLowerCase())].value.replace(/^\\s*?Question\\s*?\\-\\s*/ig,'').replace(/^\\s*/,'').replace(/\\s*$/,'');
                    return appliesto;
                }
            }
            if( propertyListLcase.includes('FullName'.toLowerCase()) ) {
                const fullname = properties[propertyListLcase.indexOf('FullName'.toLowerCase())].value.replace(/^\\s*/,'').replace(/\\s*$/,'');
                return fullname;
            }
            if( /\\.(?:categories|elements)\\s*?\\[\\s*?.*?\\s*?\\]\\s*?$/ig.test(itemName) ) {
                const refItemName = itemName.replace(/\\.(?:categories|elements)\\s*?\\[\\s*?.*?\\s*?\\]\\s*?$/ig,'');
                const refItemProperties = propertiesData[refItemName];
                const refItemPropertyListLcase = refItemProperties.map(a=>a.name.toLowerCase());
                if( refItemPropertyListLcase.includes('FullName'.toLowerCase()) ) {
                    const fullname = refItemProperties[refItemPropertyListLcase.indexOf('FullName'.toLowerCase())].value.replace(/^\\s*/,'').replace(/\\s*$/,'');
                    return fullname;
                }
            }
            return null
        } else if( /^\\s*?Pages\\./.test(itemName) ) {
            // "pages" - usually tickets are not issued for pages, skip
            return null
        } else
            return null;
    }
    function getJobNumberProperty(tableEl,errBannerEl) {
        const promise = new Promise(function(resolve,reject){
            const rowsEl = Array.from(tableEl.querySelectorAll('tr'));
            const rowBannerEl = rowsEl[0];
            const rowsWithHdataEl = rowsEl.filter(function(tr){ const cols = Array.from(tr.querySelectorAll('td')); if(cols.length>1) { return /^\\s*?(?:(?:mdd|mdm|hdata)\\.)?Properties\\s*?$/ig.test(sanitizeCellText(cols[1].textContent)); } else return false; });
            if( (rowsWithHdataEl.length>0)&&(!!rowBannerEl) ) {
                const propertiesColIndices = [];
                const isAPropertiesColumn = s => /^(?:(?:&#32;)|(?:\\s))*?(?:Custom)\\s*?properties(?:(?:&#32;)|(?:\\s))*?(?:(?:&#40;)|(?:\\())*?.*?(?:(?:&#42;)|(?:\\)))*?(?:(?:&#32;)|(?:\\s))*?$/ig.test(s);
                Array.from(rowBannerEl.querySelectorAll('td')).map(cellEl=>sanitizeCellText(cellEl.innerText||cellEl.textContent).replace(/^\\s*?\\(\\s*?(?:Left|Right)\\s*?MDD\\s*?\)\s*/ig,'')).map((colText,colIndex)=>{if(colIndex<2)return false;if(isAPropertiesColumn(colText))return colIndex;else return false;}).forEach(e=>{if(!!e)propertiesColIndices.push(e);});
                const colsEl = Array.from(rowsWithHdataEl[0].querySelectorAll('td'));
                const propertiesData = {};
                const itemNameColIndex = 1;
                const cols = Array.from(colsEl).map(cellEl=>sanitizeCellText(cellEl.innerText||cellEl.textContent).replace(/^\\s*?\\(\\s*?(?:Left|Right)\\s*?MDD\\s*?\)\s*/ig,''));
                const itemName = cols[itemNameColIndex];
                const properties = [];
                propertiesColIndices.forEach(colIndex=>{
                    properties.push(...parsePropertiesText(cols[colIndex]));
                });
                if( !!propertiesData[itemName] ) throw new Error(`grabbing properties for jira connections: duplicate row at #${i}:  ${itemName}`);
                //propertiesData[itemName] = properties.reverse(); // we reverse the order so that if we find the first matching property with indexOf it comes from the last column that stands for the right, the newer mdd
                const propertyCellContent = properties.reduce(function(acc,e){return ({...acc,[e.name]:e.value});},{});
                return resolve(propertyCellContent['JobNumber']);
            } else return null;
        });
        return promise;
    }
    function init(event){
        let errorBannerEl;
        try {
            errorBannerEl = event.detail.errorBannerEl;
        } catch(e) {
            throw e;
        }
        try {
            /* jira suggestions */
            /* https://materialplus.atlassian.net/jira/software/c/projects/P123456/issues/?jql=project%20%3D%20%22P123456%22%20AND%20%28resolution%3Dunresolved%29%20AND%20%28not%20%28status%20in%20%28Resolved%2CDone%2CClosed%29%29%29%20AND%20%28not%20%28status%20in%20%28%22Ready%20for%20Stage%22%2C%22Need%20more%20Information%22%29%29%29%20ORDER%20BY%20key%20ASC */
            /* import urllib.parse */
            /* print('https://materialplus.atlassian.net/jira/software/c/projects/P123456/issues/?jql='+(urllib.parse.quote(urllib.parse.unquote('project%20%3D%20%22P123456%22%20AND%20%28resolution%3Dunresolved%29%20AND%20%28not%20%28status%20in%20%28Resolved%2CDone%2CClosed%29%29%29%20AND%20%28not%20%28status%20in%20%28%22Ready%20for%20Stage%22%2C%22Need%20more%20Information%22%29%29%29%20ORDER%20BY%20key%20ASC'), safe=''))) */

            const pluginHolderEl = event.detail.pluginHolderEl;
            const tableEl = event.detail.tableEl;
            const bannerEl = document.createElement('div');
            bannerEl.className = 'mdmreport-layout-plugin mdmreport-banner mdmreport-banner-jirasuggestions';
            bannerEl.innerHTML = '<legend>Jira - ticket suggestion</legend>';
            const divBannerHolderEl = document.createElement('div');
            const clickmeRevealBannerEl = document.createElement('a');
            clickmeRevealBannerEl.setAttribute('href','#!');
            clickmeRevealBannerEl.setAttribute('onclick','javascript: return false;');
            clickmeRevealBannerEl.textContent = "   (show)"
            clickmeRevealBannerEl.addEventListener('click',function(event){event.preventDefault();event.stopPropagation();bannerHolderPromiseResolve({bannerHolderEl:divBannerHolderEl,tableEl,errorBannerEl});clickmeRevealBannerEl.remove();return false;});
            bannerEl.querySelector('legend').append(clickmeRevealBannerEl);
            bannerEl.append(divBannerHolderEl);
            pluginHolderEl.append(bannerEl);
            try {
                document.removeEventListener('mdmreport-oninit',init);
            } catch(ee) {}
        } catch(e) {
            try {
                errorBannerEl.innerHTML = errorBannerEl.innerHTML + `Error: ${e}<br />`;
            } catch(ee) {};
            try {
                document.removeEventListener('mdmreport-oninit',init);
            } catch(ee) {}
            throw e;
        }
    }
    function run(  { getJiraUrl, tableEl, errorBannerEl, clearUp } ) {
        try {
            const rowsEl = tableEl.querySelectorAll('tr');
            clearUp();
            const propertiesData = {};
            const itemNameColIndex = 1;
            const diffFlagColIndex = 0;
            const propertiesColIndices = [];
            const isAPropertiesColumn = s => /^(?:(?:&#32;)|(?:\\s))*?(?:Custom)\\s*?properties(?:(?:&#32;)|(?:\\s))*?(?:(?:&#40;)|(?:\\())*?.*?(?:(?:&#42;)|(?:\\)))*?(?:(?:&#32;)|(?:\\s))*?$/ig.test(s);
            const isTemporarilyMovedRow = s => /^\\s*?\\(\\s*?moved\\s*?\\)\\s*?$/ig.test(s);
            Array.prototype.forEach.call(rowsEl,function(rowEl,i) {
                const colsEl = rowEl.querySelectorAll('td');
                const cols = Array.from(colsEl).map(cellEl=>sanitizeCellText(cellEl.innerText||cellEl.textContent).replace(/^\\s*?\\(\\s*?(?:Left|Right)\\s*?MDD\\s*?\)\s*/ig,''));
                if( i==0 ) {
                    const colsWithProperties = cols.map((colText,colIndex)=>{if(colIndex<2)return false;if(isAPropertiesColumn(colText))return colIndex;else return false;});
                    colsWithProperties.forEach(e=>{if(!!e)propertiesColIndices.push(e);});
                } else {
                    const itemName = cols[itemNameColIndex];
                    const diffFlag = cols[diffFlagColIndex];
                    if( isTemporarilyMovedRow(diffFlag) )
                        return;
                    const properties = [];
                    propertiesColIndices.forEach(colIndex=>{
                        properties.push(...parsePropertiesText(cols[colIndex]));
                    });
                    if( !!propertiesData[itemName] ) throw new Error(`grabbing properties for jira connections: duplicate row at #${i}:  ${itemName}`);
                    propertiesData[itemName] = properties.reverse(); // we reverse the order so that if we find the first matching property with indexOf it comes from the last column that stands for the right, the newer mdd
                }
            });
            Array.prototype.forEach.call(rowsEl,function(rowEl,i) {
                const colsEl = Array.from(rowEl.querySelectorAll('td'));
                const colAddEl = document.createElement('td');
                colAddEl.classList.add('mdmrep-diff-jiraaddon-col');
                if(i===0) {
                    /* header row */
                    colAddEl.textContent = "Jira - possible ticket lookup link"
                } else {
                    if( (colsEl.length>=2) ) {
                        const possibleItemName = itemNameLookup(sanitizeCellText(colsEl[1].textContent),propertiesData);
                        if( !!possibleItemName && (typeof possibleItemName==='string') && (possibleItemName.length>0) ) {
                            const linkurl = getJiraUrl(possibleItemName);
                            const linkEl = document.createElement('a');
                            linkEl.setAttribute('href',linkurl);
                            linkEl.setAttribute('_target','blank');
                            linkEl.textContent = decodeURIComponent(linkurl);
                            colAddEl.append(linkEl);
                        }
                    }
                }
                rowEl.append(colAddEl);
            });
        } catch(e) {
            try {
                errorBannerEl.innerHTML = errorBannerEl.innerHTML + `Error: ${e}<br />`;
            } catch(ee) {};
            throw e;
        }
    }
    function go( { bannerHolderEl, tableEl, errorBannerEl } ) {
        try {
            const bannerContentEl = document.createElement('div');
            const propertyJobNumber = '123456';
            bannerContentEl.innerHTML = '<form method="_POST" action="#!" onSubmit="javascript: return false;" class="mdmreport-controls"><fieldset class="mdmreport-controls"></fieldset></form>';
            Array.prototype.forEach.call(bannerContentEl.querySelectorAll('form'),function(formEl){formEl.addEventListener('submit',function(event){event.preventDefault();event.stopPropagation();return false;});});
            bannerContentEl.querySelector('fieldset').innerHTML = '<div class="mdmreport-controls-group"><label>PROJECT_NUM:  </label><input type="text" value="P123456" /></div><div class="mdmreport-controls-group"><label>Base url:  </label><input type="text" value="https://materialplus.atlassian.net/jira/software/c/projects/P123456/issues/?jql=" /></div></div><div class="mdmreport-controls-group"><label>JQL:  </label><input type="text" value="project = &quot;P123456&quot; AND ((summary~&quot;<<QUESTIONNAME>>&quot;) OR (summary~&quot;<<QUESTIONSHORTNAME>>&quot;) OR (question~&quot;&#92;&quot;<<QUESTIONWANAME>>&#92;&quot;&quot;)) AND (resolution=unresolved) AND (not (status in (Resolved,Done,Closed))) AND (not (status in (&quot;Ready for Stage&quot;,&quot;Need more Information&quot;))) ORDER BY key ASC" /></div><div><input type="button" value="Run" /><p style="color: #555;"><small>Hint: you can use these keywords that will be replaced with question name: &lt;&lt;QUESTIONFULLNAME&gt;&gt;, &lt;&lt;QUESTIONSHORTNAME&gt;&gt;, &lt;&lt;QUESTIONNAME&gt;&gt;, &lt;&lt;QUESTIONWANAME&gt;&gt;.</small></p></div>'.replaceAll('123456',propertyJobNumber);
            const inp1El = bannerContentEl.querySelector('fieldset').querySelectorAll('input')[0];
            const inp2El = bannerContentEl.querySelector('fieldset').querySelectorAll('input')[1];
            const inp3El = bannerContentEl.querySelector('fieldset').querySelectorAll('input')[2];
            inp1El.addEventListener('change',function(event){ event.preventDefault(); inp2El.value = inp2El.value.replace(/(\\/projects\\/)([\\w\\-]+)(\\/)/,`$1${inp1El.value}$3`); inp2El.dispatchEvent(new Event('change')); inp3El.value = inp3El.value.replace(/(\\bproject\\b\\s*?=\\s*?"\\s*?)([\\w\\-]+)(\\s*?")/,`$1${inp1El.value}$3`); inp3El.dispatchEvent(new Event('change')); return false; });
            inp1El.addEventListener('keypress',function(event){  inp1El.dispatchEvent(new Event('change'));});
            inp2El.addEventListener('keypress',function(event){  inp2El.dispatchEvent(new Event('change'));});
            inp3El.addEventListener('keypress',function(event){  inp3El.dispatchEvent(new Event('change'));});
            inp1El.addEventListener('keyup',function(event){  inp1El.dispatchEvent(new Event('change'));});
            inp2El.addEventListener('keyup',function(event){  inp2El.dispatchEvent(new Event('change'));});
            inp3El.addEventListener('keyup',function(event){  inp3El.dispatchEvent(new Event('change'));});
            Promise.resolve().then(function(){getJobNumberProperty(tableEl,errorBannerEl).then(function(val){ const propertyJobNumber = `P${`${val}`.replace(/^\\s*?(P?)(\\d\\w+)\\s*?$/,'$2')}`; inp1El.value = propertyJobNumber; inp1El.dispatchEvent(new Event('change')); });});
            const submitEl = bannerContentEl.querySelector('fieldset').querySelectorAll('input[type="button"]')[0];
            submitEl.addEventListener('click',function(event){
                event.preventDefault();
                try {
                    const val2 = inp2El.value;
                    const val3 = inp3El.value;
                    const prepJiraString = function(jiraStr,itemName) { let name = itemName; let shortName = itemName; let fullName = itemName; let waName = itemName; if(/^\\s*?(DT_)(\\w+)$/.test(itemName)) { name = itemName.replace(/^\\s*?(DT)_(\\w+)$/,'$2'); shortName = name; waName = `${'DT'}. ${name}`; } else if(/^\\s*?(DV)_(\\w+)$/.test(itemName)) { /* all good */ } else if(/^\\s*?([a-zA-Z]+[0-9]+\\w*?)_(\\w+)$/.test(itemName)) { name = itemName.replace(/^\\s*?([a-zA-Z]+[0-9]+\\w*?)_(\\w+)$/,'$2'); shortName = itemName.replace(/^\\s*?([a-zA-Z]+[0-9]+\\w*?)_(\\w+)$/,'$1'); waName = `${shortName}. ${name}`; }; return jiraStr.replaceAll('<<QUESTIONFULLNAME>>',fullName).replaceAll('<<QUESTIONSHORTNAME>>',shortName).replaceAll('<<QUESTIONWANAME>>',waName).replaceAll('<<QUESTIONNAME>>',name); };
                    const getJiraUrl = function(itemName) { return `${decodeURIComponent(val2)}${encodeURIComponent(prepJiraString(val3,itemName))}`; };
                    if( !validDomains.map(a=>a.toLowerCase()).includes((new URL(getJiraUrl(''))).hostname.toLowerCase()) )
                        throw new Error(`Not valid jira domain! It has to be in this list: [ ${validDomains.join(', ')} ], or, update the code, it's easy; search for "validDomains"`);
                    runPromiseResolve(  { getJiraUrl, tableEl, errorBannerEl, clearUp } );
                } catch(e) {
                    try {
                        errorBannerEl.innerHTML = errorBannerEl.innerHTML + `Error: ${e}<br />`;
                    } catch(ee) {};
                    throw e;
                }
                return false;
            });
            function clearUp() { /* bannerContentEl.remove(); */ bannerContentEl.innerHTML = 'Done, see the right most column in the table'; };
            bannerHolderEl.append(bannerContentEl);
        } catch(e) {
            try {
                errorBannerEl.innerHTML = errorBannerEl.innerHTML + `Error: ${e}<br />`;
            } catch(ee) {};
            try {
                document.removeEventListener('mdmreport-oninit',init);
            } catch(ee) {}
            throw e;
        }
    }
    runPromise.then(run);
    bannerHolderPromise.then(go);
    document.addEventListener('mdmreport-oninit',init);
})();
    /* === end of jira connection js === */
</script>
    """

    TEMPLATE_HTML_JSONDIFF_STYLES = """
    something
    """

    TEMPLATE_HTML_COPYBANNER = """
AP
    """

    TEMPLATE_HTML_TABLE_BEGIN = """
<div class="wrapper">
<table class="mdmreport-table"><tbody>
"""

    TEMPLATE_HTML_TABLE_END = """
</tbody></table></div>
"""

    TEMPLATE_HTML_BEGIN = """

<!doctype html>
<html lang="">
<head>
      <meta charset="UTF-8">
      <meta http-equiv="X-UA-Compatible" content="IE=edge">
      <meta name="viewport" content="width=device-width">
      <title>{ReportTitle}</title>
      <style>{TEMPLATE_HTML_CSS_NORMALIZECSS}</style>
      <style>
      {TEMPLATE_HTML_STYLES}
      {TEMPLATE_HTML_STYLES_TABLE}
      </style>
      <script>window.mdmreporttype = '{mdmreporttype}';</script>
      {ADD_SCRIPTS}
</head>
<body class="mdmreportpage mdmreportpage-type-{mdmreporttype}">
<header class="header">
    <div class="container">
        <p>MDM Report</p>
    </div>
</header>
<div class="main">
    <div class="container">
        <h1>{ReportHeading}</h1>
        <div class="mdmreport-banner mdmreport-banner-global">{banner}</div>
        <div class="error error-banner" id="error_banner"></div>
        <div class="mdmreport-layout-plugin-placeholder" id="mdmreport_plugin_placeholder"></div>
    """.format(
        ReportTitle = fields_File_ReportTitle,
        mdmreporttype = fields_mdmreporttype,
        TEMPLATE_HTML_CSS_NORMALIZECSS = TEMPLATE_HTML_CSS_NORMALIZECSS,
        TEMPLATE_HTML_STYLES = TEMPLATE_HTML_STYLES,
        TEMPLATE_HTML_STYLES_TABLE = TEMPLATE_HTML_STYLES_TABLE,
        ReportHeading = fields_File_ReportHeading,
        banner = ''.join( [ '<p>{content}</p>'.format(content=val(content)) for content in fields_File_ReportInfo ] ),
        ADD_SCRIPTS = '{allscripts}{fieldsreportscripts}{diffscripts}'.format(allscripts=TEMPLATE_HTML_SCRIPTS,fieldsreportscripts=TEMPLATE_HTML_FIELDSREPORT_SCRIPTS if fields_mdmreporttype=='MDDFields' else '',diffscripts=TEMPLATE_HTML_JSONDIFF_SCRIPTS if fields_mdmreporttype=='MDDDiff' else '')
    )

    TEMPLATE_HTML_END = """
        </div>
    </div>
    <footer class="footer">
        <div class="container">{TEMPLATE_HTML_COPYBANNER}</div>
    </footer>
</body>
</html>
    """.format(
        TEMPLATE_HTML_COPYBANNER = TEMPLATE_HTML_COPYBANNER
    )

    report_contents_headerrow = '<tr class="mdmreport-record">{columns}</tr>'.format(
        columns = ''.join(['<td class="mdmreport-contentcell">{col}</td>'.format(col=val(col)) for col in (report['ColumnHeaders'] if 'ColumnHeaders' in report else [''])])
    );

    report_contents = ''.join( [ '<tr class="mdmreport-record">{columns}</tr>'.format(
        columns = ''.join(['<td class="mdmreport-contentcell">{col}</td>'.format(col=val(col)) for col in (row or [''])])
    ) for row in (report['Records'] if 'Records' in report else [['']]) ] )

    report_contents = '{table_begin}{table_header_row}{table_contents}{table_end}'.format(
        table_begin = TEMPLATE_HTML_TABLE_BEGIN,
        table_header_row = report_contents_headerrow,
        table_contents = report_contents,
        table_end = TEMPLATE_HTML_TABLE_END
    );

    return '{begin}{report_contents}{end}'.format(
        begin = TEMPLATE_HTML_BEGIN,
        report_contents = report_contents,
        end = TEMPLATE_HTML_END
    )


if __name__ == "__main__":
	start_time = datetime.utcnow()
	input_json = None
	if len(sys.argv)>1:
		input_json = sys.argv[1]
	if input_json==None:
		raise Exception("Create HTML report: Input file is not specified")
	if not os.path.isfile(input_json):
		raise Exception("Create HTML report: Input file is missing")
	print("Creating a report in html...\n")
	print("Loading input JSON data...\n")
	f = open(input_json)
	print("Reading JSON...\n")
	report = json.load(f)
	print("Creating output layout...\n")
	output = create_html(report)
	report_file_name = re.sub(r'\.json\s*?$','.html',input_json)
	print("Writing results...\n")
	with open(report_file_name,'w', encoding="utf-8") as output_file:
		output_file.write(output)
	end_time = datetime.utcnow()
	#elapsed_time = end_time - start_time
	print("Finished") # + str(elapsed_time)
