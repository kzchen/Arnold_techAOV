#/// arnold_tech_pass_v036 ///#

### Description ###
## This script is to create AOV tech pass system like mental ray contribution passes
## This script is still deving/improving
## really welcome anyone can give/ mail me any comments and suggestions
## Thanks! :)
## Kenzie Chen | kenziec@themill.com  


### bugs fix ###
#01. fix unexpected runtime Error when assigning AOV name


### add ###



#// load lib
import pymel.core as pm
import sys
import copy
import math

#// check if current render is Arnold
if( pm.getAttr( 'defaultRenderGlobals.currentRenderer' ) != 'arnold' ):
   pm.confirmDialog( t="Error", message="Please use Arnold render", icon='critical' )
   sys.exit( "Please use Arnold render!" )
                  
import mtoa.aovs as aovs


#// declare ui 
uiLayout = {}

#// declaire global variable
prefixAOV = 'mtoa_constant_'
isProgress = False
sel = []

    
''' =============== sub-function =============== '''
#// check if any object is seleted
def isSelEmpty(*args):
    ## access the global "sel"
    global sel
    
    sel = pm.ls( sl=True, dag=True, type='mesh' )   
    if( sel == [] ):
       pm.confirmDialog(t="Error", message="No Object is selected", icon='critical')
       return 0
    
    return 1 

    
#// check is selection has unsupport type
def isObjType(*args):
    global sel
    
    tmpList = [ o.getParent() for o in sel if not(pm.nodeType(o) == 'mesh' or pm.nodeType(o) == 'nurbsSurface') ]
    
    tmpStr = ''
    for s in tmpList:
        tmpStr = tmpStr + s + ','
            
    if( len(tmpList) > 0 ):
        pm.confirmDialog(t="Error", message= tmpStr + " are not mesh or nurbsSurface", icon='critical')
        return 0
    
    return 1


#// add Color/ String attributes
def addUserAttr( obj, attrType ):
    if( attrType == 'float3' ):
       pm.addAttr( obj, longName=(prefixAOV+'idcolor'), niceName='idcolor', usedAsColor=True, attributeType='float3' )
       pm.addAttr( obj, longName=(prefixAOV+'r'), attributeType='float', parent=(prefixAOV+'idcolor') )
       pm.addAttr( obj, longName=(prefixAOV+'g'), attributeType='float', parent=(prefixAOV+'idcolor') )
       pm.addAttr( obj, longName=(prefixAOV+'b'), attributeType='float', parent=(prefixAOV+'idcolor') )
    elif( attrType == 'string' ):
      pm.addAttr( obj, longName=(prefixAOV+'Id'), niceName='id_name', dataType='string' )
      
    return 1

          
#// Creates AOV render pass
def addAOV( name ): 
    aovName = 'id_' + name
    
    try:
        aovs.AOVInterface().addAOV( aovName )
        
    except:
        print "exception Error for addAOV!"
        
    finally:
        aovNode = aovs.AOVInterface().getAOVNode( aovName )
        pm.addAttr( aovNode, longName='isID', niceName='ai_ID', attributeType='bool', defaultValue=1 )
        aovNode.setAttr( 'isID', lock=True )

    return 1
        
    
#// add AOV Attribute for objects
def doAddAOVAttr(*args):
    if( ( isSelEmpty() and isObjType() ) == False ):
        return 0
        
    aovName = pm.textFieldButtonGrp( 'txtBtnAddAttr', query=True, text=True )
    if( len(aovName) == 0 ):
        pm.confirmDialog( t='warning', message='AOV name field is empty!', icon='warning' )
        return 0
    
    for obj in sel:                  
       if( not( obj.hasAttr(prefixAOV+'Id') ) ):
           addUserAttr( obj, 'string' )
                   
       #// add AOV name as Attribute
       pm.PyNode( obj + '.' + prefixAOV + 'Id' ).set( 'id_'+aovName )
    
       #// skip loop if the input textfield is empty
       if( len(aovName) == 0 ): continue
            
       #// add AOV render pass
       #// check if AOV already existing
       if( len( pm.ls('aiAOV_id_'+aovName) ) == 0 ):
           addAOV( aovName )
           
    return 1


def doAddColorAttr( inColor ): 
    if( ( isSelEmpty() and isObjType() ) == False ):
        return 0
        
    for obj in sel:
       if( not( obj.hasAttr(prefixAOV+'idcolor') ) ):
           addUserAttr( obj, 'float3' )                       
       #// assign color
       pm.PyNode( obj + '.' + prefixAOV + 'idcolor' ).set( inColor )
              
    return 1
   
   
#// delete custom mtoa* attributes
def doDelAttrAOV(*args):
    if( isSelEmpty() and isObjType() == False ):
        return 0
    
    for obj in sel:
        if( obj.hasAttr(prefixAOV+'Id') ):
            pm.deleteAttr( obj, attribute=prefixAOV+'Id' )
        if( obj.hasAttr(prefixAOV+'idcolor') ):
            pm.deleteAttr( obj, attribute=prefixAOV+'idcolor' )
            
    return 1


#// delete unused AOVs
def doDelEmptyAOVs(*args):
    updateAOVStrAttr()
    
    attr_color = [ 'obj_R', 'obj_G', 'obj_B', 'obj_W' ]
    sceneAOVs = aovs.AOVInterface().getAOVNodes(names=True)
    #// filter AOV
    id_aov_sets = [ node for name, node in sceneAOVs if name.find('id_') == 0 ]
     
    for aov in id_aov_sets:
        count = 0
        for attr in attr_color:
            if( pm.PyNode(aov).hasAttr(attr) ):
                if( len(pm.PyNode(aov + '.' + attr).get()) == 0 ):
                    count += 1
                                                      
        if count == 4:
            pm.delete(aov)
            doUpdateScnAOV(1)
            
    return 1


#// update/ collect each AOVs containing objects list
def updateAOVStrAttr(*args):
    #// custom Attr
    attr_R = 'obj_R'
    attr_G = 'obj_G'
    attr_B = 'obj_B'
    attr_W = 'obj_W'    
    
    sceneAOVs = aovs.AOVInterface().getAOVNodes(names=True)
    
    #// filter AOV
    id_aov_sets = [ node for name, node in sceneAOVs if( name.find('id_') == 0 and node.hasAttr('isID') ) ]
    
    #// loop each AOV to add custom Attr
    #// this loop can resore AOVs RGB obj lists if AOVs has been deleted acidentally   
    for aov in id_aov_sets:
        if( not( pm.PyNode(aov).hasAttr(attr_R) ) ):
            pm.addAttr( aov, longName=attr_R, niceName='R', dataType='string' )
            
        if( not( pm.PyNode(aov).hasAttr(attr_G) ) ):
            pm.addAttr( aov, longName=attr_G, niceName='G', dataType='string' )
            
        if( not( pm.PyNode(aov).hasAttr(attr_B) ) ):
            pm.addAttr( aov, longName=attr_B, niceName='B', dataType='string' )
            
        if( not( pm.PyNode(aov).hasAttr(attr_W) ) ):
            pm.addAttr( aov, longName=attr_W, niceName='W', dataType='string' )
                                                     
        #// initialize                            
        pm.PyNode(aov+'.'+attr_R).set('')
        pm.PyNode(aov+'.'+attr_G).set('')
        pm.PyNode(aov+'.'+attr_B).set('')
        pm.PyNode(aov+'.'+attr_W).set('')
        
    #// collect mesh in scene           
    listMesh = pm.ls(type='mesh')
    if( len(listMesh) == 0 ): return "no mesh in scene"
      
    maxValue = len(listMesh)
    global isProgress
    
    pm.progressWindow( title='AOV Update Calculation', progress=0, maxValue=maxValue , isInterruptable=True, status='calculating: 0%' )
    isProgress = True

    for amount, mesh in enumerate(listMesh, 0):
        try:
            pm.progressWindow( edit=True, progress=amount, status=('calculating: ' + str( math.ceil(100 * amount/ maxValue) ) + '%') )
            if pm.progressWindow( query=True, isCancelled=True ) :
                break
            
            #// test if obj has both id and idcolor attrs ##
            if( mesh.hasAttr('mtoa_constant_Id') and mesh.hasAttr('mtoa_constant_idcolor') ):
                #print mesh
                idName = mesh.mtoa_constant_Id.get()
                idColor = mesh.mtoa_constant_idcolor.get()
                
                if( idColor == (1.0, 0.0, 0.0) ):
                    AOV_attr_obj = 'aiAOV_' + idName + '.' + attr_R
                    
                if( idColor == (0.0, 1.0, 0.0) ):
                    AOV_attr_obj = 'aiAOV_' + idName + '.' + attr_G
                    
                if( idColor == (0.0, 0.0, 1.0) ):
                    AOV_attr_obj = 'aiAOV_' + idName + '.' + attr_B
                    
                if( idColor == (1.0, 1.0, 1.0) ):
                    AOV_attr_obj = 'aiAOV_' + idName + '.' + attr_W
                
                #// test if shape's aov is not existing in scene AOV
                if( len( pm.ls( 'aiAOV_' + idName ) ) == 0 ):
                    addAOV( idName.split('_')[1] )
                    continue
                
                #// write to object_list Attr     
                pm.PyNode(AOV_attr_obj).set( pm.PyNode(AOV_attr_obj).get() + mesh.getParent() + ';' )
        except:
            print "unexpected error during update: ", mesh
            continue 
    
    pm.progressWindow( endProgress=1 )
    isProgress = False       
    return 1
          

def doStopUpdateAOV(*args):
    if isProgress:
        pm.progressWindow(endProgress=1)
    return 1


#// update scene id/ AOV
def doUpdateScnAOV(type, *args):
    #// first, update string attr in each AOV
    if type == 0:
        updateAOVStrAttr()
    
    # next, update AOV list
    AOVList = []
    sceneAOVs = aovs.AOVInterface().getAOVNodes(names=True)
    for aovName, aovNode in sceneAOVs:
        if( aovName.find('id_') == 0 and aovNode.hasAttr('isID') ):
            AOVList.append( str(aovName) )
    
    enumUIParent = pm.optionMenu( 'enumAOVList', q=True, parent=True )
    
    curr_aov = pm.optionMenu( 'enumAOVList', q=True, value=True )
    if curr_aov == None: return
  
    pm.deleteUI('enumAOVList')
        
    pm.optionMenu( 'enumAOVList', bgc=[0.2, 0.2, 0.2], label="AOVs: ", width=120, parent=enumUIParent )
    for aov in AOVList:
        pm.menuItem( aov )
    
    if( ( len(curr_aov) != 0 ) and ( len( pm.ls(aovs.AOVInterface().getAOVNode(curr_aov)) ) != 0 ) ):
        pm.optionMenu( 'enumAOVList', e=True, value=curr_aov )
        
    #// if curr_aov is not existing...

    return 1

def doSelObjInAOV(*args):
    curr_aov = pm.optionMenu( 'enumAOVList', q=True, value=True )

    if( curr_aov == None ): return 0
    
    #// [:-1] means remove last string, an empty space   
    pm.select(cl=True)

    if( pm.checkBox( 'chk_R', query=True, v=True ) ):
        pm.select( pm.PyNode('aiAOV_'+curr_aov).obj_R.get().split(';')[:-1], add=True )
        
    if( pm.checkBox( 'chk_G', query=True, v=True ) ):
        pm.select( pm.PyNode('aiAOV_'+curr_aov).obj_G.get().split(';')[:-1], add=True )
                
    if( pm.checkBox( 'chk_B', query=True, v=True ) ):
        pm.select( pm.PyNode('aiAOV_'+curr_aov).obj_B.get().split(';')[:-1], add=True )
                
    if( pm.checkBox( 'chk_W', query=True, v=True ) ):
        pm.select( pm.PyNode('aiAOV_'+curr_aov).obj_W.get().split(';')[:-1], add=True )
        
    return 1
            
                        
def doDelAOV(*args):
    curr_aov = pm.optionMenu( 'enumAOVList', q=True, value=True )
    if curr_aov == None: return 0
    
    aovs.AOVInterface().removeAOVs(curr_aov)
    #// type = 1, no need to update indof insude AOV node
    doUpdateScnAOV(1)
    
    return 1;

#// AOVs list output
def outputAOVLists(aov_info):
    fileObj = pm.fileDialog2( fileMode=0, fileFilter="aav (*.aav)", caption="Save AOV lists as" )
    
    try:   
        f = file( fileObj[0], 'w' )
    except:
        return 0
        
    f.write( '*** AOVs list ***\n*** %s *** \n' % ( pm.sceneName() ) )
    f.write(aov_info)
    f.close()
    
    #// return file with path
    return 1


def doBuildAOVFromFile(*args):
    fileObj = pm.fileDialog2( fileMode = 1, fileFilter="aav(*.aav)", caption="Open AOV lists as" )
    try:
        f = file( fileObj[0], 'r' )
    except:
        return 0
    
    # print f.readline().split('\n')[0][0:18]
    if( f.readline().split('\n')[0] != "*** AOVs list ***" ):
        pm.confirmDialog( t='File Error!', message='not a valid file!', b=['OK'], icon='critical' )
        return 0
        
    color_tag = { 'obj_R':(1, 0, 0), 'obj_G':(0, 1, 0), 'obj_B':(0, 0, 1), 'obj_W':(1, 1, 1) }
    error_obj = []
    aov_list = []
    for num, line in enumerate( f, 2 ):
        #// remove '\n' at the end
        line = line[:-1]
        
        #// skip remark line and empty line
        if( line[0:3] == '***' or len(line) == 0 ):
            continue
            
        ##// parsing text into node, attribute, and value
        #// test if the object list is empty
        if( len( line.split('--')[1] ) == 0 ):
            continue
             
        #// aov attribute    
        aov_attr = line.split('--')[0].split('.')[1]
        #// aov id name
        aov_name = line.split('--')[0].split('.')[0]
        
        #// collect all aov id name from file   
        if( len(aov_list) == 0):
            aov_list.append(aov_name)
            
        if( aov_list[len(aov_list)-1] != aov_name ):
            aov_list.append(aov_name)
            print aov_list
              
        '''if( pm.ls('aiAOV_id_' + aov_name) == 0 ):
            addAOV(aov_name.split('_')[1])'''
            
        
           
        #// value: objet lists       
        aov_attr_val = line.split('--')[1].split(';')
        
        ##// loop object in list
        for o in aov_attr_val:
            
            #// test if ref objects have same name but under different ref naming space when multi importing assets 
            try:
                pm.ls(o)
            except:
                print "A: ", o
                error_obj.append(o)
                continue
                                
            #// test if obj is existing in scene
            if( len(pm.ls(o)) == 0 ):
                print "B: ", o
                error_obj.append(o)
                continue
                                
            obj = pm.ls(o)[0]                
            #// test if obj has Id Attr 
            if not obj.hasAttr(prefixAOV+'Id'):
                addUserAttr( obj.getShape(), 'string' )
                
            #// test if obj has idcolor Attr    
            if not obj.hasAttr(prefixAOV+'idcolor'):
                addUserAttr( obj.getShape(), 'float3' )
            
            pm.PyNode( obj + '.' + prefixAOV + 'Id' ).set( aov_name )
            pm.PyNode( obj + '.' + prefixAOV + 'idcolor' ).set( color_tag[aov_attr] )
            
    pm.confirmDialog( t='Complete!', message='Rebuild AOV --> Obj is done!', b=['OK'], icon='information' )
    
    if( len(error_obj) > 0 ):
        pm.confirmDialog( t='Objects Missing!', message=('Original Objects Missing Target: \n======================\n%s' % ''.join(error_obj) ), b=['OK'], icon='critical' )
              
    return 1



#// rebuild object Attr from AOVs
#// when updateing model assets
def doSaveAOVData(*args):
    color_tag = [ ['obj_R',(1, 0, 0)], ['obj_G', (0, 1, 0)], ['obj_B', (0, 0, 1)], ['obj_W', (1, 1, 1)] ]
    
    sceneAOVs = aovs.AOVInterface().getAOVNodes(names=True)

    #// collect custom id AOVs
    id_aov_sets = [ ( name, node ) for name, node in sceneAOVs if( name.find('id_') == 0 and node.hasAttr('isID') ) ]
        
    aov_info = str()
    
    for aov_name, aov_node in id_aov_sets:
        aov_info += '\n'
        for cl_attr, cl_val in color_tag:
            # print '%s: %s, %s' % (aov_name, cl_attr, cl_val)
            list_obj = pm.PyNode( aov_node + "." + cl_attr ).get().split(';')[:-1]
            
            #// convert to a list to save out as a file
            aov_info += ( aov_name + '.' + cl_attr + '--' + ';'.join(list_obj) + '\n' ) 
 
    #// write to file
    if( outputAOVLists(aov_info) == 0 ):
        pm.confirmDialog( t='Cancel!', message='Svaing is cancel!', b=['OK'], icon='information' )
        return 0
    
    pm.confirmDialog( t='Save Complete!', message='Save AOVs Info is done!', b=['OK'], icon='information' )
 
    return 1                                         


#// search derformer shape and copy attrs from original shape 
def doCopyAttrToDeformShape(*args): 
    global sel
    
    if( ( isSelEmpty() and isObjType() ) == False ):
        return 0
        
    deformer_shp = []
    for shp in sel:
        if( len( shp.tweakLocation.inputs() ) == 0 ):
            continue
        
        #// collect deformer shape
        print "deformer shape found: ", shp
        deformer_shp.append(shp)
        
        trnsf = shp.getParent()
        orig_shp = trnsf.getShape()
        
            
        #// check if custom Attr are existing
        if( orig_shp.hasAttr( prefixAOV + 'Id' ) ):
            #// cehck if deformer shape has custom attrs already
            if( shp.hasAttr(prefixAOV+'Id') ):
                continue
                
            #// copy attr to deformer shape    
            addUserAttr( shp, 'string' )

            value = pm.PyNode(orig_shp + '.' + prefixAOV + 'Id').get()
            pm.PyNode( shp + '.' + prefixAOV + 'Id' ).set(value)
            
            
        if( orig_shp.hasAttr( prefixAOV + 'idcolor' ) ):
            #// cehck if deformer shape has custom attrs already
            if( shp.hasAttr(prefixAOV+'idcolor') ):
                continue
                
            #// copy attr to deformer shape    
            addUserAttr( shp, 'float3' ) 
            value = pm.PyNode(orig_shp + '.' + prefixAOV + 'idcolor').get()
            pm.PyNode( shp + '.' + prefixAOV + 'idcolor' ).set(value)
            
    if( len(deformer_shp) == 0 ):
        pm.confirmDialog( t='Infomation', message='No Object has deformed shape!', b=['OK'], icon='information' )
        return 1
        
    pm.confirmDialog( t='Complete!', message='Attributes have been transfered to deforemder shapes!', b=['OK'], icon='information' )
    
    return 1


#// resore AOVs System
def doRestoreAOVSys(*args):
    #// read file
    #// parsing text
    #// rebuild/ build AOVs
        
    return 1

           
#// create shading network
def doIDShdNetwork(*args):
    ## check if the shading network is existing
    shdName = 'idSetup'

    if( len( pm.ls(shdName + "_SHD") ) ) != 0:
        pm.confirmDialog(t="Warning", message="The shader has been existed!", icon='warning')
        return 0
        
    #// aiUserDataColor
    dataColor = pm.shadingNode('aiUserDataColor', asUtility=True, name=shdName+'DataColor')
    dataColor.colorAttrName.set('idcolor')
    
    #// aiUserDataString
    dataString = pm.shadingNode('aiUserDataString', asUtility=True, name=shdName+'DataString')
    dataString.stringAttrName.set('Id')
    
    #// aiWriteColor
    writeColor = pm.shadingNode('aiWriteColor', asUtility=True, name=shdName+'WriteColor')
    
    #// aiUtility
    aiIDShd = pm.shadingNode('aiUtility', asShader=True, name=shdName+'_SHD')
    idSetup_SHD_SG = pm.sets( renderable=True, noSurfaceShader=True, empty=True, name="idSetup_SHD_SG" )
    
    #// connect material to shading group 
    aiIDShd.outColor >> idSetup_SHD_SG.surfaceShader
    
    aiIDShd.shadeMode.set(2)
    
    #// connections
    dataColor.outColor >> writeColor.input
    dataString.outValue >> writeColor.aovName
    writeColor.outColor >> aiIDShd.color     
          

def assinIDShdNetwork(*args):
    global sel 
    sel = pm.ls( sl=True, dag=True, type='mesh' )
    for mesh in sel:
        pm.sets( 'idSetup_SHD_SG', e=True, fe=mesh )


          
''' ===============  main function =============== ''' 
def main():
    #// check if the current renderer is Arnold
    global sel   
    if( pm.window('ArnoldAOVSetup', exists=True) ):
       pm.deleteUI('ArnoldAOVSetup')    
  
    uiLayout['window'] = pm.window('ArnoldAOVSetup', menuBar=True, title='Setup Arnold Tech IDs', sizeable=False, h=400, w=250)
    uiLayout['mainLayout'] = pm.columnLayout( columnAlign='left', columnAttach=['left', 0] )
    
    
    #// NO.1 column
    uiLayout['ui_sub1'] = pm.frameLayout( label='01. AOV name setup', width=250, bgc=[0.2, 0.2, 0.2], cl=False, cll=True, borderStyle='in', p=uiLayout['mainLayout'] )
    
    pm.text( label='--- Input AOV name for selected objects ---', align='center', bgc=[0.1, 0.1, 0.1], parent=uiLayout['ui_sub1'] )
    
    #// AOV name/ Attribute assign
    uiLayout['ui_sub1a'] = pm.rowLayout( nc=4, p=uiLayout['ui_sub1'] )
    pm.text( label='AOV name:', parent=uiLayout['ui_sub1a'] )
    pm.textField( text='id_', bgc=[0.4, 0, 0 ], editable=False, width=25, parent=uiLayout['ui_sub1a'] )
    pm.text( label='+', parent=uiLayout['ui_sub1a'] )   
    uiLayout['addObjAttr'] = pm.textFieldButtonGrp( 'txtBtnAddAttr', label='', text='', buttonLabel='  Assign  ', cw3=[0, 80, 0], buttonCommand=doAddAOVAttr, parent=uiLayout['ui_sub1a'] )        
    
    pm.separator(h=8, w=250, style='single', p=uiLayout['mainLayout'])
     

    #// NO.2 column   
    uiLayout['ui_sub2'] = pm.frameLayout( label='02. AOV color setup', width=250, bgc=[0.2, 0.2, 0.2], cl=False, cll=True, borderStyle='in', p=uiLayout['mainLayout'] )
    
    pm.text( label='--- Pick AOV color for selected objects ---', align='center', bgc=[0.1, 0.1, 0.1], parent=uiLayout['ui_sub2'] )

    uiLayout['ui_sub2_color'] = pm.rowColumnLayout( w=250, nc=4, cw=[(1,60), (2,60), (3,60), (4,60)], parent=uiLayout['ui_sub2'] )
    pm.button(l='Red', ebg=True, bgc=[1, 0, 0], c=lambda *args:doAddColorAttr( [1, 0, 0] ), parent=uiLayout['ui_sub2_color'])
    pm.button( label='Green', ebg=True, bgc=[0, 1, 0], c=lambda *args:doAddColorAttr( [0, 1, 0] ), parent=uiLayout['ui_sub2_color'] )
    pm.button( label='Blue', ebg=True, bgc=[0, 0, 1], c=lambda *args:doAddColorAttr( [0, 0, 1] ), parent=uiLayout['ui_sub2_color'] )
    pm.button( label='White', ebg=True, bgc=[1, 1, 1], c=lambda *args:doAddColorAttr( [1, 1, 1] ), parent=uiLayout['ui_sub2_color'] )
    
    pm.separator(h=8, w=250, style='single', p=uiLayout['mainLayout'])

   
    #// NO.3 column
    uiLayout['ui_sub3'] = pm.frameLayout( label='03. Shader setup', width=250, bgc=[0.2, 0.2, 0.2], cl=False, cll=True, borderStyle='in', p=uiLayout['mainLayout'] )
    pm.text( label='--- Create Shading Network ---', align='center', bgc=[0.1, 0.1, 0.1], parent=uiLayout['ui_sub3'] )
    uiLayout['ui_sub3_btn'] = pm.rowColumnLayout( w=250, nc=2, cw=[(1,120), (2,120)], parent=uiLayout['ui_sub3'] )
    pm.button( label=' Create !', ebg=True, c=doIDShdNetwork, parent=uiLayout['ui_sub3_btn'] )
    pm.button( label=' Assign !', ebg=True, c=assinIDShdNetwork, parent=uiLayout['ui_sub3_btn'] )
    
    pm.separator(h=8, w=250, style='single', p=uiLayout['mainLayout'])
    
    
    #// NO.4 column
    uiLayout['ui_sub_4'] = pm.frameLayout( label='* Advance Control *', bgc=[0.3, 0.3, 0.1], width=250, cl=True, cll=True, borderStyle='in', p=uiLayout['mainLayout'] )
    pm.text( label='--- AOVs & Objects Attr operation ---', align='center', bgc=[0.1, 0.1, 0.1], parent=uiLayout['ui_sub_4'] )
    
    uiLayout['ui_sub_4_aov'] = pm.frameLayout( label='** AOVs Control', bgc=[0.25, 0.2, 0.2], width=300, cl=True, cll=True, borderStyle='in', p=uiLayout['ui_sub_4'] )  
    uiLayout['ui_sub_4_aov_1'] = pm.rowLayout( nc=3, p=uiLayout['ui_sub_4_aov'] )
        
    #// setup enum list
    pm.button( label=' Update AOV ', ebg=True, bgc=[0.5, 0.5, 0.2], c=lambda *args:doUpdateScnAOV(0), parent=uiLayout['ui_sub_4_aov_1'] )
    pm.button( label=' stop ', ebg=True, bgc=[0.5, 0.2, 0.2], c=doStopUpdateAOV, parent=uiLayout['ui_sub_4_aov_1'] ) 
    pm.optionMenu( 'enumAOVList', label="AOVs: ", width=120, bgc=[0.2, 0.2, 0.2], parent=uiLayout['ui_sub_4_aov_1'] )
    pm.menuItem('')

            
    uiLayout['ui_sub_4_aov_2'] = pm.rowLayout( nc=5, cw=[(1,90), (2,35), (3,35), (4,35), (5,35)], p=uiLayout['ui_sub_4_aov'] )
    pm.button( label=' Select Objects ', ebg=True, c=doSelObjInAOV, parent=uiLayout['ui_sub_4_aov_2'] )
    pm.checkBox( 'chk_R', label='R', v=True, ebg=True, bgc=[1, 0, 0] )
    pm.checkBox( 'chk_G', label='G', v=True, ebg=True, bgc=[0, 1, 0] )
    pm.checkBox( 'chk_B', label='B', v=True, ebg=True, bgc=[0, 0, 1] )
    pm.checkBox( 'chk_W', label='W', v=True, ebg=True, bgc=[1, 1, 1] )
    
    uiLayout['ui_sub_4_aov_3'] = pm.rowLayout( nc=3, cw=[(1,50), (2,100), (3,100)], p=uiLayout['ui_sub_4_aov'] )
    
    pm.button( label=' Del AOV ', c=doDelAOV, bgc=[0.7, 0, 0], parent=uiLayout['ui_sub_4_aov_3'] )
    
    #// delete buttons group ##
    pm.button( label=' Del Empty AOVs! ', ebg=True, c=doDelEmptyAOVs, parent=uiLayout['ui_sub_4_aov_3'] )
    pm.button( label=' Del Attributes! ', ebg=True, c=doDelAttrAOV, parent=uiLayout['ui_sub_4_aov_3'] )
    
    #// DATA rebuild
    #// to copy shape attributes to new update model assets 
    uiLayout['ui_sub_4_data'] = pm.frameLayout( label='** Attr Rebuild', bgc=[0.2, 0.25, 0.2], width=300, cl=True, cll=True, borderStyle='in', p=uiLayout['ui_sub_4'] )
    
    uiLayout['ui_sub_4_data_1'] = pm.rowColumnLayout( w=250, nc=2, cw=[(1,120), (2,120)], parent=uiLayout['ui_sub_4_data'] )
    pm.button( label=' Save AOVs Info ', ebg=True, c=doSaveAOVData, parent=uiLayout['ui_sub_4_data_1'] )
    pm.button( label=' Restore AOVs Info ', ebg=True, c=doBuildAOVFromFile, parent=uiLayout['ui_sub_4_data_1'] )
    
    uiLayout['ui_sub_4_data_2'] = pm.rowColumnLayout( w=250, nc=2, cw=[(1,120), (2,120)], parent=uiLayout['ui_sub_4_data'] )
    pm.button( label=' Deformer Shape Fix ', ebg=True, c=doCopyAttrToDeformShape, parent=uiLayout['ui_sub_4_data_2'] )
    
    # pm.button( label=' Restore AOV system ', enable=False, bgc=[0.25,0.25,0.25], ebg=True, c=doRestoreAOVSys, parent=uiLayout['ui_sub_4_data_2'] )
    
    
    # print uiLayout
    pm.showWindow( uiLayout['window'] )
    
main()
