import pymel.core as pm

# check if current render is Arnold
if( pm.getAttr( 'defaultRenderGlobals.currentRenderer' ) != 'arnold' ):
   pm.confirmDialog(t="Error", message="Please use Arnold render", icon='critical')
   sys.exit("Please use Arnold render!")

import copy
import mtoa.aovs as aovs
import functools as fn
import sys


# declare ui library
uiWidgets = {}
prefixAOV = 'mtoa_constant_'

sel = []

''' ===== sub-function ===== '''
## check if any object is seleted
def isSelEmpty(*args):
    ## access the global "sel"
    global sel
    
    sel = pm.ls( sl=True, dag=True, type='shape' )      
    if( sel == [] ):
       pm.confirmDialog(t="Error", message="No Object is selected", icon='critical')
       return 0
    
    return 1 

    
## check is selection has unsupport type
def isObjType(*args):
    tmpList = [ o.getParent() for o in sel if not(pm.nodeType(o) == 'mesh' or pm.nodeType(o) == 'nurbsSurface') ]
    
    tmpStr = ''
    for s in tmpList:
        tmpStr = tmpStr + s + ','
            
    if( len(tmpList) > 0 ):
        pm.confirmDialog(t="Error", message= tmpStr + " are not mesh or nurbsSurface", icon='critical')
        return 0
    
    return 1


## add Color/ String attributes
def addUserAttr(obj, attrType):
    if( attrType == 'float3' ):
       pm.addAttr( obj, longName=(prefixAOV+'idcolor'), niceName='idcolor', usedAsColor=True, attributeType='float3' )
       pm.addAttr( obj, longName=(prefixAOV+'r'), attributeType='float', parent=(prefixAOV+'idcolor') )
       pm.addAttr( obj, longName=(prefixAOV+'g'), attributeType='float', parent=(prefixAOV+'idcolor') )
       pm.addAttr( obj, longName=(prefixAOV+'b'), attributeType='float', parent=(prefixAOV+'idcolor') )
    elif( attrType == 'string' ):
      pm.addAttr( obj, longName=(prefixAOV+'Id'), niceName='id_name', dataType='string' )
      
    return 1

          
## Creates AOV render pass
def addAOV( aovName ):
    _aov = 'id_' + aovName
    if( not(aovs.AOVInterface().getAOVNode(_aov) == _aov ) ):
        aovs.AOVInterface().addAOV( _aov )
        
    return 1
        


## add AOV Attribute for objects
def doAddAOVAttr( *args ):
    if( ( isSelEmpty() and isObjType() ) == False ):
        return 0
    
    for obj in sel:
       print obj                  
       if( not( obj.hasAttr(prefixAOV+'Id') ) ):
           addUserAttr( obj, 'string' )
          
       aovName = pm.textFieldButtonGrp( 'txtBtnAddAttr', query=True, text=True )
             
       # add AOV name as Attribute
       pm.PyNode( obj + '.' + prefixAOV + 'Id' ).set( 'id_'+aovName )
    
       # skip loop if the input textfield is empty
       if( len(aovName) == 0 ): continue
            
       # add AOV render pass
       # check if AOV already existing
       if( len( pm.ls('aiAOV_id_'+aovName) ) == 0 ):
           addAOV( aovName )
           
    return 1


def doAddColorAttr( inColor, *args ):
    if( ( isSelEmpty() and isObjType() ) == False ):
        return 0
        
    for obj in sel:
       if( not( obj.hasAttr(prefixAOV+'idcolor') ) ):
           addUserAttr( obj, 'float3' )                       
       # assign color
       pm.PyNode( obj + '.' + prefixAOV + 'idcolor' ).set( inColor )
              
    return 1
   



## 
def doDelAttrAOV(*args):
    if( isSelEmpty() and isObjType() == False ):
        return 0
    
    for obj in sel:
        if( obj.hasAttr(prefixAOV+'Id') ):
            pm.deleteAttr( obj, attribute=prefixAOV+'Id' )
        if( obj.hasAttr(prefixAOV+'idcolor') ):
            pm.deleteAttr( obj, attribute=prefixAOV+'idcolor' )
            
    return 1


## 
def doDelEmptyAOVs(*args):
    updateAOVStrAttr()
    # collect all AOVS in scene
    sceneAOVs = aovs.AOVInterface().getAOVNodes(names=True)
    # filter AOV
    id_aov_sets = [ node for name, node in sceneAOVs if node.find('_id_') == 5 ]
    for aov in id_aov_sets:
        if( pm.PyNode(aov).hasAttr('object_list') ):
            if( len(pm.PyNode(aov).object_list.get()) == 0 ):
                pm.delete (aov)

    return 1


def updateAOVStrAttr( *args ):
    strAttr = 'object_list'
    sceneAOVs = aovs.AOVInterface().getAOVNodes(names=True)
    
    # filter AOV
    id_aov_sets = [ node for name, node in sceneAOVs if node.find('_id_') == 5 ]
    
    for aov in id_aov_sets:
        if( not( pm.PyNode(aov).hasAttr(strAttr) ) ):
            pm.addAttr( aov, longName=strAttr, dataType='string' )
        pm.PyNode(aov+'.'+strAttr).set('')
    
    
    listMesh = pm.ls(type='mesh')
    amount = 0.0
    maxValue = len(listMesh)
    pm.progressWindow( title='AOV Update Calculation', progress=amount, maxValue=maxValue , isInterruptable=True, status='calculating: 0%' )
    
    for mesh in listMesh:
        amount =  amount + 1
        pm.progressWindow( edit=True, progress=amount, status=('calculating: ' + str( 100 * amount/ maxValue) + '%') )
        if( mesh.hasAttr('mtoa_constant_Id') ):
            idName = mesh.mtoa_constant_Id.get()
            currAOVStrAttr = 'aiAOV_' + idName + '.' + strAttr
            pm.PyNode(currAOVStrAttr).set( pm.PyNode(currAOVStrAttr).get() + mesh + ';' )
    
    pm.progressWindow(endProgress=1)       
    return 1
          

## update scene id/ AOV
def doUpdateScnAOV(*args):
    # first, update string attr in each AOV
    updateAOVStrAttr()
    
    # next, update AOV list
    AOVList = []
    index = 0
    sceneAOVs = aovs.AOVInterface().getAOVNodes(names=True)
    for aovName, aovNode in sceneAOVs:
        if( aovName.find('id_') == 0 ):
            AOVList.append( str(aovName) )
            index =  index + 1
    
    enumUIParent = pm.optionMenu( 'enumAOVList', q=True, parent=True )
    pm.deleteUI('enumAOVList')
        
    pm.optionMenu( 'enumAOVList', bgc=[0.2, 0.2, 0.2], label="AOVs: ", width=120, parent=enumUIParent )
    for aov in AOVList:
        pm.menuItem( aov )

    return 1
    

def doSelObjInAOV(*args):
    curr_aov = pm.optionMenu( 'enumAOVList', q=True, value=True )
    
    # [:-1] means remove last string, an empty space
    curr_aov_obj = pm.PyNode('aiAOV_'+curr_aov).object_list.get().split(';')[:-1]
    
    pm.select(cl=True)
    pm.select(curr_aov_obj)
    
    return 1
            
                        
def doDelAOV(*args):
    curr_aov = pm.optionMenu( 'enumAOVList', q=True, value=True )
    aovs.AOVInterface().removeAOVs(curr_aov)
    return 1;


## create shading network
def doIDShdNetwork(*args):
    ## check if the shading network is existing
    shdName = 'idSetup'

    if( len( pm.ls(shdName + "_SHD") ) ) == 0:
      # aiUserDataColor
      dataColor = pm.shadingNode('aiUserDataColor', asShader=True, name=shdName+'DataColor')
      dataColor.colorAttrName.set('idcolor')
     
      # aiUserDataString
      dataString = pm.shadingNode('aiUserDataString', asShader=True, name=shdName+'DataString')
      dataString.stringAttrName.set('Id')
     
      # aiWriteColor
      writeColor = pm.shadingNode('aiWriteColor', asShader=True, name=shdName+'WriteColor')
      
      # aiUtility
      aiIDShd = pm.shadingNode('aiUtility', asShader = True, name=shdName+'_SHD')
    
      # connections
      dataColor.outColor >> writeColor.input
      dataString.outValue >> writeColor.aovName
      writeColor.outColor >> aiIDShd.color     
  
    else:
      pm.confirmDialog(t="Warning", message="The shader has been existed!", icon='warning')
      


      
''' =====  main function ===== '''

def main(*args):
    ## check if the current renderer is Arnold
       
    if( pm.window('ArnoldAOVSetup', exists=True) ):
       pm.deleteUI('ArnoldAOVSetup')    
  
    uiWidgets['window'] = pm.window('ArnoldAOVSetup', menuBar=True, title='Setup Arnold Contribution AOV', sizeable=False, h=250, w=250)
    uiWidgets['mainLayout'] = pm.columnLayout( columnAlign='left', columnAttach=['left', 5] )
    
    
    ### NO.1 column
    uiWidgets['sub1'] = pm.columnLayout( p=uiWidgets['mainLayout'] )
    pm.text( label='01. Type AOV name for selected objects.', parent=uiWidgets['sub1'] )
    
    ## AOV name/ Attribute assign
    uiWidgets['sub1a'] = pm.rowLayout( nc=4, p=uiWidgets['sub1'] )
    pm.text( label='AOV name:', parent=uiWidgets['sub1a'] )
    pm.textField( text='id_', bgc=[0.4, 0, 0 ], editable=False, width=25, parent=uiWidgets['sub1a'] )
    pm.text( label='+', parent=uiWidgets['sub1a'] )   
    uiWidgets['addObjAttr'] = pm.textFieldButtonGrp( 'txtBtnAddAttr', label='', text='', buttonLabel='  Assign  ', cw3=[0, 80, 0], buttonCommand='doAddAOVAttr()', parent=uiWidgets['sub1a'] )        

    ## delete buttons group ##
    uiWidgets['sub1b'] = pm.rowLayout( nc=2, p=uiWidgets['sub1'] )
    pm.button( label=' Delete Attributes! ', ebg=True, c=doDelAttrAOV, parent=uiWidgets['sub1b'] )
    pm.button( label=' Delete Empty AOVs! ', ebg=True, c=doDelEmptyAOVs, parent=uiWidgets['sub1b'] )
    
    ## ----------------------------------------------
    pm.separator(h=20, w=250, p=uiWidgets['sub1'])
    
    ## control Scene AOVs group ##
    uiWidgets['sub1c'] = pm.rowLayout( nc=2, p=uiWidgets['sub1'] )
        
    ## setup enum list
    pm.button( label=' Update AOV ', ebg=True, bgc=[0.5, 0.5, 0.0], c=doUpdateScnAOV, parent=uiWidgets['sub1c'] ) 
    pm.optionMenu( 'enumAOVList', label="AOVs: ", width=120, bgc=[0.2, 0.2, 0.2], parent=uiWidgets['sub1c'] )
            
    uiWidgets['sub1d'] = pm.rowLayout( nc=2, p=uiWidgets['sub1'] )
    pm.button( label=' Select Objects in AOV ', ebg=True, c=doSelObjInAOV, parent=uiWidgets['sub1d'] )
    pm.button( label=' Delete AOV ', ebg=True, c=doDelAOV , parent=uiWidgets['sub1d'] )

    ## ----------------------------------------------   
    pm.separator(h=20, w=250, p=uiWidgets['sub1'])
   

    ### NO.2 column   
    uiWidgets['sub2'] = pm.columnLayout( p=uiWidgets['mainLayout'] )
    pm.text( label='02. Pick AOV color for selected objects.', parent=uiWidgets['sub2'] )

    uiWidgets['sub2_color'] = pm.rowColumnLayout( w=300, nc=4, cw=[(1,50), (2,50), (3,50), (4,50)], parent=uiWidgets['sub2'] )
    pm.button(l='Red', ebg=True, bgc=[1, 0, 0], c=fn.partial(doAddColorAttr, [1, 0, 0]), p=uiWidgets['sub2_color'])
    pm.button( label='Green', ebg=True, bgc=[0, 1, 0], c=fn.partial(doAddColorAttr, [0, 1, 0]), p=uiWidgets['sub2_color'] )
    pm.button( label='Blue', ebg=True, bgc=[0, 0, 1], c=fn.partial(doAddColorAttr, [0, 0, 1]), p=uiWidgets['sub2_color'] )
    pm.button( label='White', ebg=True, bgc=[1, 1, 1], c=fn.partial(doAddColorAttr, [1, 1, 1]), p=uiWidgets['sub2_color'] )
    pm.separator(h=20, w=250, p=uiWidgets['sub2'])

   
    ### NO.3 column
    uiWidgets['sub3'] = pm.rowLayout( nc=2, p=uiWidgets['mainLayout'] )
    pm.text( label='03. Create Shading Network.', parent=uiWidgets['sub3'] )
    pm.button( label='   Create!   ', ebg=True, c=doIDShdNetwork, parent=uiWidgets['sub3'] )
  
  
    #print uiWidgets
    pm.showWindow( uiWidgets['window'] )
    
main()
