#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May  1 11:29:46 2019

@author: wangj
"""

Pathref = '/gpfs/data/xyz/jianmin/VNPdata/VNP43IA4/' #'/hunter/data1/wangj/LSP_VIIMOD/VNP43IA4/'
Pathqa = '/gpfs/data/xyz/jianmin/VNPdata/VNP43IA2/'
Pathout = '/gpfs/data/xyz/jianmin/VNPdata/composite3d_ndwi/'
Tiles = ['h09v05'] #'h27v07', 'h10v05', 'h12v04', 'h13v04'
Years = list(range(2015, 2019)) #[2016, 2017, 2018]
Outstyle = 0  ### IF 0, the output are separated files of each is a composite (day);;;  if 1, the output is the one BIP file for a tile year
Nyear = 2 #### 1 for the current year and 2 for the previous and proceeding half year and the current year. 
Nday = 3  ## How many days composite
Nrow = 2400
Ncol = 2400
FILL = 32767






def main(pathref, pathqa, pathout, tiles, years, outstyle, nyear, nday):
    import sys
    import numpy as np 
    import os
    import time

    if not os.path.exists(pathout):
        os.mkdir(pathout)
    years = sorted(years) ### or years.sort()
    for tile in tiles:
        for year in years:
            dds, yys = dayandyear(year, years, nyear, nday)
            
            for dd, yy, in zip(dds, yys):
                dates = [str(yy) + str(item).zfill(3) for item in dd+np.arange(nday)]
#                    outfile = pathout + 'VIIRS_VI.'+dates[0]+'.' + tile + '.BIP.gz'
                outfile = '%sVIIRS_VI.%s.%s.BIP.gz' % (pathout, dates[0], tile)
                
                if (os.path.isfile(outfile)) and (os.path.getsize(outfile) > 50): 
                    print("      %s exists and file size is > 50 kb" % outfile)
                    continue
                else:
                    print("generating %s" % outfile)
                    
                #files_ref = [pathref + 'VNP43IA4.A' + item + '.'+ tile + '.001.h5' for item in dates]
                #[pathref + 'VNP43IA4.A' + item1 + '.h27v07.001.h5' + item2 for item1, item2 in zip(dates, a)]
                #files_qa = [pathqa + 'VNP43IA2.A' + item + '.'+ tile + '.001.h5' for item in dates]
                files_ref = ["%sVNP43IA4.A%s.%s.001.h5" % (pathref, item, tile) for item in dates ]
                files_qa = ["%sVNP43IA2.A%s.%s.001.h5" % (pathqa, item, tile) for item in dates ]
                
                start = time.process_time()
                Success = manage_composite(files_ref, files_qa, outfile)
                end = time.process_time()
                print(end-start)
                
                if Success != 1 :
                    print('Compositing has problems with day %s in year %s' % (dd, yy))
                    sys.exit(1)
                            
        if outstyle == 1:
            #reognize the output files
            for year in years:
                #outfile = pathout + 'VIIRS_VI.'+str(year)+'.' + tile + '.year' + str(nyear) + '.BIP.gz'
                outfile = '%sVIIRS_VI.%s.%s.year%s.BIP.gz' % (pathout, year, tile, nyear)
                if os.path.isfile(outfile) : 
                    continue
                dds, yys = dayandyear(year, years, nyear, nday)                    
                
                # files=[pathout + 'VIIRS_VI.'+ str(yy) + str(dd).zfill(3) +'.' + tile + '.BIP.gz' for yy, dd in zip(yys, dds)]
                files=['%sVIIRS_VI.%s%s.%s.BIP.gz' % (pathout, yy, str(dd).zfill(3), tile) for yy, dd in zip(yys, dds)]
                Success = stackgzfiles(files, outfile)
                    
                        

def dayandyear(year, years, nyear, nday):
    import numpy as np
    DDs=np.arange(1, 366, nday)
    YYs=np.array([year]*len(DDs))
    dds=DDs
    yys=YYs
    if nyear == 2:
        Nfile = len(DDs)
        Nfilehalf = Nfile//2
        if year-1 not in years:
            dds = np.concatenate((DDs[Nfilehalf:Nfile], DDs), axis=0)
            yys = np.concatenate((np.array([year-1]*(Nfile-Nfilehalf)), YYs), axis=0)
            
        if year+1 not in years:
            dds = np.concatenate((dds, DDs[0:Nfilehalf]), axis=0)
            yys = np.concatenate((yys, np.array([year+1]*Nfilehalf)), axis=0)   
        
    return(dds, yys)

   


def manage_composite(files_ref, files_qa, outfile):
    import gzip 
#    import struct 
    import numpy as np
    import time
    
    with gzip.open(outfile, 'wb') as f:
    #RES = np.zeros(Nrow, Ncol, 4)
        start1 = time.process_time()
        EVI2, NDVI, NDWI, QA = index_calculate(files_ref, files_qa)
        end1 = time.process_time()
        print("                           index calculation finished, spent %f s" % (end1-start1))
        if EVI2 is None:
            #bytes_write = struct.pack('hhhh', int(FILL), int(9), int(FILL), int(FILL))
            #[f.write(bytes_write) for i in range(Nrow) for j in range(Ncol)]
            res=np.full((Nrow, Ncol, 4), FILL, dtype=np.int16)
            res[:,:,1]=9
        
        else:
            start2 = time.process_time()
            evi2, qa, ndvi, ndwi = COMPOSITE(EVI2, NDVI, NDWI, QA)
            end2 = time.process_time()
            print("                           composition finished, spent %f s" % (end2-start2))
            res=np.stack((evi2, qa, ndvi, ndwi), axis=2)
            #[f.write(struct.pack('hhhh', tmpevi2, tmpqa, tmpndvi, tmpndwi)) for tmpevi2, tmpqa, tmpndvi, tmpndwi in zip(np.nditer(evi2), np.nditer(qa), np.nditer(ndvi), np.nditer(ndwi))]

        f.write(res.tostring())


    return(1)
        

        
        
        
def index_calculate(REF_files, QA_files) : 
    import numpy as np
    import os
    import h5py
        
    [print("%s is missed" % file) for file in REF_files if not os.path.isfile(file)]
    QA_files=[file for file, file_ref in zip(QA_files, REF_files) if os.path.isfile(file_ref)]
    REF_files=[file for file in REF_files if os.path.isfile(file)]
    
    n=len(REF_files)
    if n > 0:  
        EVI2 = np.full((Nrow, Ncol, n), FILL, dtype=np.int16)
        NDVI = np.full((Nrow, Ncol, n), FILL, dtype=np.int16)
        NDWI = np.full((Nrow, Ncol, n), FILL, dtype=np.int16)
        QA = np.full((Nrow, Ncol, n), 4, dtype=np.int16)
        k=0
        for k in range(n):
            file_ref = REF_files[k]
            file_qa = QA_files[k]
            ### Read Files
            hand_ref = h5py.File(file_ref, 'r')
            # https://lpdaac.usgs.gov/resources/e-learning/working-daily-nasa-viirs-surface-reflectance-data/
            ## fileMetadata = hand_ref['HDFEOS INFORMATION']['StructMetadata.0'].value.split()
            ## fileMetadata = [m.decode('utf-8') for m in fileMetadata]                 # Clean up file metadata
            ## fileMetadata[0:33]                                     
                   
#            grids = list(hand_ref['HDFEOS']['GRIDS'])
#            h5_objs = []            # Create empty list
#            hand_ref.visit(h5_objs.append) # Walk through directory tree, retrieve objects and append to list
#            # Search for SDS with 1km or 500m grid
#            all_datasets = [obj for grid in grids for obj in h5_objs if isinstance(f[obj],h5py.Dataset) and grid in obj] 
#            all_datasets
            
            ref_I1 = hand_ref['/HDFEOS/GRIDS/VIIRS_Grid_BRDF/Data Fields/Nadir_Reflectance_I1'][()] #.size and np.shape() to check the size
            ref_I2 = hand_ref['/HDFEOS/GRIDS/VIIRS_Grid_BRDF/Data Fields/Nadir_Reflectance_I2'][()]
            ref_I3 = hand_ref['/HDFEOS/GRIDS/VIIRS_Grid_BRDF/Data Fields/Nadir_Reflectance_I3'][()]
            qa_I1 = hand_ref['/HDFEOS/GRIDS/VIIRS_Grid_BRDF/Data Fields/BRDF_Albedo_Band_Mandatory_Quality_I1'][()] #.size and np.shape() to check the size
            qa_I2 = hand_ref['/HDFEOS/GRIDS/VIIRS_Grid_BRDF/Data Fields/BRDF_Albedo_Band_Mandatory_Quality_I2'][()]
            #qa_I3 = hand_ref['/HDFEOS/GRIDS/VIIRS_Grid_BRDF/Data Fields/BRDF_Albedo_Band_Mandatory_Quality_I3'][()]
            hand_ref.close()
            
            hand_qa = h5py.File(file_qa, 'r')
            snow = hand_qa['/HDFEOS/GRIDS/VIIRS_Grid_BRDF/Data Fields/Snow_BRDF_Albedo'][()]
            water = hand_qa['/HDFEOS/GRIDS/VIIRS_Grid_BRDF/Data Fields/BRDF_Albedo_LandWaterType'][()]
            hand_qa.close()
            
            #(ref_I2[0,0] - ref_I3[0,0])/ (ref_I2[0,0] + 2.4*ref_I3[0,0] + 10000.0)
            ### Calculate index
            
            evi2 = 25000.0 * (ref_I2 - ref_I1)/ (ref_I2 + 2.4*ref_I1 + 10000)
            ndvi = 10000.0*(ref_I2-ref_I1)/(ref_I2+ref_I1)
            ndwi = 10000.0*(ref_I2-ref_I3)/(ref_I2+ref_I3)
            #mask = (ref_I1 <=0) | (ref_I1 >= 10000) | (ref_I2 <=0) | (ref_I2 >= 10000) | (ref_I3 <=0) | (ref_I3 >= 10000)
            #ref_I1_valid = np.ma.MaskedArray(ref_I1, mask)
            
            tmpind = (ref_I1 <=0) | (ref_I1 >= 10000) | (ref_I2 <=0) | (ref_I2 >= 10000)  
            evi2[tmpind] = FILL
            ndvi[tmpind] = FILL
            tmpind = (ref_I3 <=0) | (ref_I3 >= 10000) | (ref_I2 <=0) | (ref_I2 >= 10000)
            ndwi[tmpind] = FILL
            
            
            ### Record QA
            #dim = ref_I1.shape
            qa = np.full((Nrow, Ncol), 0, dtype=np.int16)
            qa[(qa_I1 != 0) | (qa_I2 != 0)] = 4
            qa[(water < 1) | (water > 2)] = 100 ### water
            qa[snow == 1]=1
            qa[(evi2 == FILL) | (ndvi==FILL) | (qa_I1 > 100) | (qa_I2 > 100)] = 9 ##FILL
            
            EVI2[:,:,k] = evi2.astype(np.int16)
            NDVI[:,:,k] = ndvi.astype(np.int16)
            NDWI[:,:,k] = ndwi.astype(np.int16)
            QA[:,:,k] = qa
            
#            VI_vec = np.vectorize(VI, otypes=[np.int16, np.int16, np.int16, np.int16])
#            evi2, ndvi, ndwi, qa = VI_vec(ref_I1, ref_I2, ref_I3, qa_I1, qa_I2, water, snow)

        return(EVI2, NDVI, NDWI, QA)
    else:
        return(None, None, None, None)
        


#def VI(r1, r2, r3, q1, q2, wr, sn):
#    if (r1 <=0) or (r1 >= 10000) or (r2 <=0) or (r2 >= 10000):
#        eevi2=FILL
#        nndvi=FILL
#    else:
#        eevi2 = 25000.0 * (r2 - r1)/ (r2 + 2.4*r1 + 10000)
#        nndvi = 10000.0*(r2-r1)/(r2+r1)
#        
#    if (r3 <=0) or (r3 >= 10000) or (r2 <=0) or (r2 >= 10000):
#        nndwi=FILL
#    else:
#        nndwi = 10000.0*(r2-r3)/(r2+r3)
#    
#    qqa=0
#    if (q1 !=0) or (q2 != 0):
#        qqa=4
#    if (wr < 1) or (wr > 2):
#        qqa = 100
#    if (sn ==1):
#        qqa=1
#    if (eevi2 == FILL) or (nndvi == FILL) or (q1 >100) or (q2 >100):
#        qqa=9
#    
#    return(eevi2, nndvi, nndwi, qqa)



#a = np.zeros([3, 3, 4])
#def func(x):
#    x[x==0]=1
#func(a[0, 0, :])

def composite(evi2, ndvi, ndwi, qa):   
    import numpy as np
    
    index = (qa == 0) & ((evi2 <-3000) | (evi2 > 10000))
    qa[index] = 9
    evi2[index]=FILL
    
    
    if any(qa == 100):
        outqa = 100
        outevi2 = FILL
        outndvi = FILL
        outndwi = FILL
    elif all(qa == 9):
        outqa = 9
        outevi2 = FILL
        outndvi = FILL
        outndwi = FILL
    else: 
        outqa = np.nanmin(qa)
        index = qa == outqa
        outevi2 = np.amax(evi2[index])
        outndvi = np.amax(ndvi[index])
        outndwi = np.amax(ndwi[index])
        
    if (outqa!=100) and (any(qa == 1)):
        outqa = 1
           
    return(outevi2, outqa, outndvi, outndwi)
    
    
def COMPOSITE(EVI2, NDVI, NDWI, QA):
    import numpy as np
    
    n=np.shape(EVI2)[2]
    outEVI2 = np.full([Nrow, Ncol], FILL, dtype=np.int16)
    outNDVI = np.full([Nrow, Ncol], FILL, dtype=np.int16)
    outNDWI = np.full([Nrow, Ncol], FILL, dtype=np.int16)
    outQA = np.full([Nrow, Ncol], 9, dtype=np.int16)
        
    index = (QA == 0) & ((EVI2 < -3000) | (EVI2 > 10000))
    QA[index] = 9
    EVI2[index]=FILL
    
    index = np.any(QA==100, axis = 2)
    outQA[index] = 100

    index = (np.logical_not(index)) & (np.any(QA<9, axis =2))
    outQA[index] = np.nanmin(QA[index], axis = 1)
    
    outQAn = np.repeat(outQA[:, :, np.newaxis], n, axis=2)
    indexqa = (QA != outQAn)
    indexqa[np.logical_not(index)] = True
    
    maskedEVI2 = np.ma.array(EVI2, mask = indexqa)
    maskedNDVI = np.ma.array(NDVI, mask = indexqa)
    maskedNDWI = np.ma.array(NDWI, mask = indexqa)
    tmpEVI2 = np.amax(maskedEVI2, axis=2)
    tmpNDVI = np.amax(maskedNDVI, axis=2)
    tmpNDWI = np.amax(maskedNDWI, axis=2)
    
#    EVI2[indexqa]=np.nan
#    NDVI[indexqa]=np.nan
#    NDWI[indexqa]=np.nan    
#    tmpEVI2 = np.nanmax(EVI2, axis=2)
#    tmpNDVI = np.nanmax(NDVI, axis=2)
#    tmpNDWI = np.nanmax(NDWI, axis=2)
    
    outEVI2[index] = tmpEVI2[index]
    outNDVI[index] = tmpNDVI[index]
    outNDWI[index] = tmpNDWI[index]
    
    
    outQA[(outQA!=100) & (np.any(QA==1, axis = 2))] = 1
    
    return(outEVI2, outQA, outNDVI, outNDWI)
    
    
        
def stackgzfiles(files, outfile):
    import gzip 
    
    with gzip.open(outfile, 'wb') as f:
        try: 
            fins = [gzip.open(file, 'rb') for file in files]
        finally:
            while True:
                [f.write(fin.read(8)) for fin in fins if True]
#                for fin in fins:
#                    bytes_write = fin.read(8)
#                    if not bytes_write:
#                        break
#                    f.write(bytes_write)
            
            for fin in fins:
                fin.close()
                
                
main(Pathref, Pathqa, Pathout, Tiles, Years, Outstyle, Nyear, Nday)        


