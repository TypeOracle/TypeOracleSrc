'''
    TypeOracle: a fuzzer for PDF Readers' script engine
    Copyright (C) 2022 Suyue Guo(guosuyue@ruc.edu.cn), Xinyu Wan(wxyxsx@ruc.edu.cn), Wei You(youwei@ruc.edu.cn)

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import mPDF

# js1 = 'app.alert("")\napp.toolbar\ntry{this.scroll()}catch(e){}\napp.toolbar\ncloseDoc(1)'
# js2 = 'app.alert("")\napp.toolbar\ntry{app.beep()}catch(e){}\napp.toolbar\ncloseDoc(1)'
# js3 = 'app.alert("")\napp.toolbar\ntry{util.charToByte()}catch(e){}\napp.toolbar\ncloseDoc(1)'
js1 = 'try{this.gotoNamedDest({})}catch(e){}\narg={}\napp.toolbar\ntry{this.gotoNamedDest(arg)}catch(e){}\napp.toolbar\ncloseDoc(1)'
js2 = 'try{this.scroll({})}catch(e){}\narg={}\napp.toolbar\ntry{this.scroll(arg)}catch(e){}\napp.toolbar\ncloseDoc(1)'
js3 = 'try{this.getIcon({})}catch(e){}\narg={}\napp.toolbar\ntry{this.getIcon(arg)}catch(e){}\napp.toolbar\ncloseDoc(1)'

mPDF.make_pdf(js1,'1.pdf')
mPDF.make_pdf(js2,'2.pdf')
mPDF.make_pdf(js3,'3.pdf')