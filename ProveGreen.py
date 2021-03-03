# -*- coding: utf-8 -*-
"""
Created on Fri Dec 25 18:06:27 2020

@author: gogliom
"""


import pandas as pd
import re
import numpy as np
import regex as re  #ATTENZIONE! DEVO IMPORTARE 3RD PARTY REGEX MODULO PERCHè QUESTO SUPPORTA I "NEGATIVE LOOKAHEAD
                    #DI LUNGHEZZA VARIABILE --> DEVO PRENDERE "VERDE" CHE NON SIA PRECEDUTO DA NUMERO O DA N° E QUESTO 
                    #E' UN NEGATIVE LOOKAHEAD DI LUNGHEZZA VARIABILE CHE VA IN ERRORE SU MODULO STANDARD DI RE
                    #CFR (https://www.reddit.com/r/learnpython/comments/d5g4ow/regex_match_pattern_not_preceded_by_either_of_two/)


def energiaVerde(Doc, PE):
    '''
    questa funzione consente di verificare se la cte prevede l'energia verde
    
    @keyword: lista di parole chiave
    @document: intero documento da esaminare
    '''

 
    
    PossiblePrice = []
    Base = []
    
    
    #Doc = convert_pdf_to_txt(Doc)
    #Doc = Doc.upper()
    
    #le inserisco come regular expression perchè non so quanti spazi ci sono e se magari c'è una new line (\s+)
    r1 = r'GREEN(?!\s+NETWORK)'
    r2 = r'(?<!NUMERO.{0,20}|N°.{0,20}|N.{0,20})VERDE'
    r3 = r'100%.{0,10}FONTI.{0,20}RINNOVABILI'
    r4 = r'SOLO.{0,20}FONT.{0,20}RINNOVABIL'
    r5 = r'OPZIONE.{0,30}RINNOVABI'
    r6 = r'SOLTANTO.{0,10}ENERGIA.{0,25}RINNOVABILI'
    r7 = r'APPROVVIGION.{0,10}IMPIANTI.{0,25}RINNOVABIL'
    r8 = r'100%.{0,20}RINNOVABIL'
    r9 = r'RINNOVABIL.{0,20}100%'
    r10 = r'100.{0,10}ENERGIA.{0,10}PULITA'
    r11 = r'ENERGIA.{0,10}PULITA.{0,10}100'
    r12 = r'ESCLUSIVAMENTE.{0,10}FONTI.{0,10}RINNOVABILI'
    r13 = r'SOLO.{0,10}FONTI.{0,10}RINNOVABILI'
    r14 = r'CORRISPETTIVO.{0,5}ENERGIA.{0,10}VERDE'
    r15 = r'INTERAMENTE.{0,50}FONT.{0,10}RINNOVABI'
    r16 = r'ESCLUSIVA.{0,50}FONT.{0,10}RINNOVABI'
    
    regex = [r1, r2 , r3, r4, r5, r6, r7, r8, r9, r10, r11, r12, r13, r14, r15, r16]
    
    regex = re.compile('|'.join(regex))
    
    
    Base = [m.start() for m in regex.finditer(Doc)]
    Base = pd.DataFrame(Base, columns = ['PositionBase'])
      
 
    regexNum1 = r'-?\s?\d+\,?\d+'
    regexNum2 = r'-?\s?\d+\.?\d+'
    
        
    regexNum = [regexNum1, regexNum2]
    
    regexNum = re.compile('|'.join(regexNum))
    
    
    NumberPos = [m.start() for m in regexNum.finditer(Doc)]
    NumberValue = regexNum.findall(Doc)
    NumberTuples = list(zip(NumberValue,NumberPos))
    
    
    PossiblePrice = pd.DataFrame(NumberTuples, columns=['Price', 'Position'])
    #converto in numero
    PossiblePrice['Price_NUM'] = PossiblePrice.apply(lambda row: row.Price.replace(",","."), axis = 1)
    PossiblePrice['Price_NUM'] = PossiblePrice.apply(lambda row: row.Price_NUM.replace(" ",""), axis = 1)
    PossiblePrice['Price_NUM'] = PossiblePrice.apply(lambda row: float(row.Price_NUM), axis = 1)
    
    #filtro numeri < 5 --> possono anche essere negativi?
    PossiblePrice = PossiblePrice[(PossiblePrice['Price_NUM'] > -0.05) & (PossiblePrice['Price_NUM'] < 5)]
    
    #elimino i numeri lunghi 2 che iniziano con zero, sono tendenzialmente date --> errori 
    PossiblePrice['Lun'] = PossiblePrice.apply(lambda row: len(row.Price.replace(" ","")), axis = 1)
    PossiblePrice['Start'] = PossiblePrice.apply(lambda row: row.Price.replace(" ","")[0], axis = 1)
    PossiblePrice = PossiblePrice[(PossiblePrice['Lun'] != 2) | (PossiblePrice['Start']!= "0")]
    PossiblePrice = PossiblePrice[PossiblePrice['Price_NUM'] != PE]

    
    
    '''
    APPROCCIO IN BASE AL QUALE CERCO €/KWH E PRENDO PAROLA PRECEDENTE, MA IN ALCUNI CASI NELLE TABELLE NON E ESPLICITATA
    EURO/KWH VICINO AL NUMERO
    ii = 0
    for ww in Doc.split():
        if "€/KWH" in ww or "EURO/KWH" in ww:
            pw = Doc.split()[ii-1]
            po = Doc.find(Doc.split()[ii-1]+" "+Doc.split()[ii])
            nn = pd.DataFrame({'Price': [pw], 'Position': [po]})
            PossiblePrice = PossiblePrice.append(nn) 
            #Positions = Positions + list(ii-1)        
        ii = ii + 1 
    #estraggo i numeri 
    PossiblePrice['Price'] = PossiblePrice.apply(lambda row: re.findall('-?\d*\,.?\d+', str(row.Price)), axis=1)
    #elimino eventuali stringe vuote
    PossiblePrice = PossiblePrice[PossiblePrice['Price'].apply(lambda row: len(row)) > 0]
    '''
    Doc[3000:3400]
    
    Base['key'] = 0
    PossiblePrice['key'] = 0
    
    Prezzo = Base.merge(PossiblePrice, how='outer')
    Prezzo['dist'] = Prezzo.apply(lambda row: row.Position - row.PositionBase, axis = 1)
    #FILTRO PER LE DISTANZE POSITIVE (IL NUMERO VIENE DOPO LA PAROLA, OPPURE NEGATIVE MOLTO PICCOLE DOVE QUINDI LA BASE VIENE IMMEDIATAMENTE DOPO )
    Prezzo = Prezzo[(Prezzo['dist'] > - 25) & (Prezzo['dist'] < 300)]
    
    #se prezzo è > 1 non è ammontare a kwh, ma mensile, quindi mi aspetto cifra tonda..
    Prezzo = Prezzo[(Prezzo['Price_NUM'] < 1) | (Prezzo['Price_NUM'] % 0.5 == 0)]
        
    
    Prezzo = Prezzo.nsmallest(1, 'dist')
    
    #creo flag Y/N oltre a prezzo 
    #se ho trovato delle parole in base ma poi non ho trovato match con prezzo, vuol dire che energia è green ma non si paga?
    if len(Base) > 0 and len(Prezzo) == 0:
        Prezzo = Prezzo.append({'FlagVerde': 'Y'}, ignore_index=True)
    elif len(Base) == 0:
        Prezzo = Prezzo.append({'FlagVerde': 'N'}, ignore_index=True)
    elif len(Base) > 0 and len(Prezzo) > 0:
        Prezzo['FlagVerde'] = "Y"
        

    return (Prezzo['FlagVerde'],Prezzo['Price_NUM'])
    
   

 
