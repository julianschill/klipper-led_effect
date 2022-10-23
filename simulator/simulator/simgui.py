# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version 3.10.1-e2e4764)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc

###########################################################################
## Class SimFrame
###########################################################################

class SimFrame ( wx.Frame ):

	def __init__( self, parent ):
		wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = u"LED Effects Simulator", pos = wx.DefaultPosition, size = wx.Size( 1060,909 ), style = wx.DEFAULT_FRAME_STYLE|wx.BORDER_DEFAULT|wx.TAB_TRAVERSAL )

		self.SetSizeHints( wx.Size( 1060,800 ), wx.DefaultSize )

		bSizer1 = wx.BoxSizer( wx.VERTICAL )

		self.m_ledpanel = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.Size( -1,-1 ), wx.TAB_TRAVERSAL )
		self.m_ledpanel.SetBackgroundColour( wx.Colour( 0, 0, 0 ) )

		bSizer1.Add( self.m_ledpanel, 1, wx.ALL|wx.EXPAND, 5 )

		bSettingsSizer = wx.BoxSizer( wx.VERTICAL )

		bSettingsSizer.SetMinSize( wx.Size( -1,500 ) )
		bSizer15 = wx.BoxSizer( wx.VERTICAL )

		self.m_panel4 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.BORDER_SIMPLE|wx.TAB_TRAVERSAL )
		bChainSettingsSizer = wx.BoxSizer( wx.HORIZONTAL )

		self.m_lblLEDs = wx.StaticText( self.m_panel4, wx.ID_ANY, u"LEDs:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_lblLEDs.Wrap( -1 )

		bChainSettingsSizer.Add( self.m_lblLEDs, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

		self.m_spinLED = wx.SpinCtrl( self.m_panel4, wx.ID_ANY, u"32", wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 1, 10000, 25 )
		bChainSettingsSizer.Add( self.m_spinLED, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

		self.m_lblShape = wx.StaticText( self.m_panel4, wx.ID_ANY, u"Shape:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_lblShape.Wrap( -1 )

		bChainSettingsSizer.Add( self.m_lblShape, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

		m_cbShapeChoices = [ u"Circle", u"Square" ]
		self.m_cbShape = wx.ComboBox( self.m_panel4, wx.ID_ANY, u"Circle", wx.DefaultPosition, wx.DefaultSize, m_cbShapeChoices, wx.CB_READONLY )
		bChainSettingsSizer.Add( self.m_cbShape, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

		self.m_lblLEDSize = wx.StaticText( self.m_panel4, wx.ID_ANY, u"Size:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_lblLEDSize.Wrap( -1 )

		bChainSettingsSizer.Add( self.m_lblLEDSize, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

		self.m_spinLEDSize = wx.SpinCtrl( self.m_panel4, wx.ID_ANY, u"15", wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 1000, 0 )
		bChainSettingsSizer.Add( self.m_spinLEDSize, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

		self.m_lblLayout = wx.StaticText( self.m_panel4, wx.ID_ANY, u"Layout: ", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_lblLayout.Wrap( -1 )

		bChainSettingsSizer.Add( self.m_lblLayout, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

		m_cbLayoutChoices = [ u"Rectangle", u"Circle", u"Triangle", u"Voron Logo" ]
		self.m_cbLayout = wx.ComboBox( self.m_panel4, wx.ID_ANY, u"Rectangle", wx.DefaultPosition, wx.DefaultSize, m_cbLayoutChoices, wx.CB_READONLY )
		self.m_cbLayout.SetSelection( 0 )
		bChainSettingsSizer.Add( self.m_cbLayout, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

		self.m_lblLines = wx.StaticText( self.m_panel4, wx.ID_ANY, u"Lines:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_lblLines.Wrap( -1 )

		bChainSettingsSizer.Add( self.m_lblLines, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

		self.m_spinLines = wx.SpinCtrl( self.m_panel4, wx.ID_ANY, u"1", wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 1000, 0 )
		bChainSettingsSizer.Add( self.m_spinLines, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

		self.m_lblDistance = wx.StaticText( self.m_panel4, wx.ID_ANY, u"Distance:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_lblDistance.Wrap( -1 )

		bChainSettingsSizer.Add( self.m_lblDistance, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

		self.m_spinDistance = wx.SpinCtrl( self.m_panel4, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, -1000, 1000, 15 )
		bChainSettingsSizer.Add( self.m_spinDistance, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )


		self.m_panel4.SetSizer( bChainSettingsSizer )
		self.m_panel4.Layout()
		bChainSettingsSizer.Fit( self.m_panel4 )
		bSizer15.Add( self.m_panel4, 0, wx.ALL, 5 )


		bSettingsSizer.Add( bSizer15, 0, wx.ALL, 5 )

		bEffectSettingsSizer = wx.BoxSizer( wx.HORIZONTAL )

		self.m_effectSettingsPanel = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.BORDER_SIMPLE|wx.TAB_TRAVERSAL )
		fg_effectSettingsSizer = wx.FlexGridSizer( 0, 2, 0, 0 )
		fg_effectSettingsSizer.SetFlexibleDirection( wx.BOTH )
		fg_effectSettingsSizer.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

		self.m_lblActive = wx.StaticText( self.m_effectSettingsPanel, wx.ID_ANY, u"Active:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_lblActive.Wrap( -1 )

		fg_effectSettingsSizer.Add( self.m_lblActive, 0, wx.ALL, 5 )

		self.m_cbActive = wx.CheckBox( self.m_effectSettingsPanel, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_cbActive.SetValue(True)
		self.m_cbActive.Enable( False )

		fg_effectSettingsSizer.Add( self.m_cbActive, 0, wx.ALL, 5 )

		self.m_lblEffect = wx.StaticText( self.m_effectSettingsPanel, wx.ID_ANY, u"Effect: ", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_lblEffect.Wrap( -1 )

		fg_effectSettingsSizer.Add( self.m_lblEffect, 0, wx.ALL, 5 )

		m_cbEffectChoices = []
		self.m_cbEffect = wx.ComboBox( self.m_effectSettingsPanel, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, m_cbEffectChoices, wx.CB_READONLY )
		self.m_cbEffect.Enable( False )

		fg_effectSettingsSizer.Add( self.m_cbEffect, 0, wx.ALL, 5 )

		self.m_lblEffectRate = wx.StaticText( self.m_effectSettingsPanel, wx.ID_ANY, u"Effect rate:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_lblEffectRate.Wrap( -1 )

		fg_effectSettingsSizer.Add( self.m_lblEffectRate, 0, wx.ALL, 5 )

		self.m_spinEffectRate = wx.SpinCtrlDouble( self.m_effectSettingsPanel, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 100, 0.000000, 0.1 )
		self.m_spinEffectRate.SetDigits( 2 )
		self.m_spinEffectRate.Enable( False )

		fg_effectSettingsSizer.Add( self.m_spinEffectRate, 0, wx.ALL, 5 )

		self.m_lblCutOff = wx.StaticText( self.m_effectSettingsPanel, wx.ID_ANY, u"Cut off:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_lblCutOff.Wrap( -1 )

		fg_effectSettingsSizer.Add( self.m_lblCutOff, 0, wx.ALL, 5 )

		self.m_spinCutOff = wx.SpinCtrlDouble( self.m_effectSettingsPanel, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 100, 0, 0.1 )
		self.m_spinCutOff.SetDigits( 2 )
		self.m_spinCutOff.Enable( False )

		fg_effectSettingsSizer.Add( self.m_spinCutOff, 0, wx.ALL, 5 )

		self.m_lblBlending = wx.StaticText( self.m_effectSettingsPanel, wx.ID_ANY, u"Blending:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_lblBlending.Wrap( -1 )

		fg_effectSettingsSizer.Add( self.m_lblBlending, 0, wx.ALL, 5 )

		m_cbBlendingChoices = []
		self.m_cbBlending = wx.ComboBox( self.m_effectSettingsPanel, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, m_cbBlendingChoices, wx.CB_READONLY )
		self.m_cbBlending.Enable( False )

		fg_effectSettingsSizer.Add( self.m_cbBlending, 0, wx.ALL, 5 )

		self.m_lblPalette = wx.StaticText( self.m_effectSettingsPanel, wx.ID_ANY, u"Palette:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_lblPalette.Wrap( -1 )

		fg_effectSettingsSizer.Add( self.m_lblPalette, 0, wx.ALL, 5 )

		bSizer17 = wx.BoxSizer( wx.VERTICAL )

		bSizer16 = wx.BoxSizer( wx.HORIZONTAL )

		m_lbPaletteChoices = []
		self.m_lbPalette = wx.ListBox( self.m_effectSettingsPanel, wx.ID_ANY, wx.DefaultPosition, wx.Size( -1,70 ), m_lbPaletteChoices, wx.LB_SINGLE|wx.VSCROLL )
		self.m_lbPalette.Enable( False )

		bSizer16.Add( self.m_lbPalette, 1, wx.ALL|wx.EXPAND, 5 )

		bSizer18 = wx.BoxSizer( wx.VERTICAL )

		self.m_btnAddColour = wx.Button( self.m_effectSettingsPanel, wx.ID_ANY, u"+", wx.DefaultPosition, wx.Size( 20,20 ), 0 )
		self.m_btnAddColour.Enable( False )

		bSizer18.Add( self.m_btnAddColour, 0, wx.ALL, 5 )

		self.m_btnRemoveColour = wx.Button( self.m_effectSettingsPanel, wx.ID_ANY, u"-", wx.DefaultPosition, wx.Size( 20,20 ), 0 )
		self.m_btnRemoveColour.Enable( False )

		bSizer18.Add( self.m_btnRemoveColour, 0, wx.ALL, 5 )

		self.m_btnColourUp = wx.Button( self.m_effectSettingsPanel, wx.ID_ANY, u"^", wx.DefaultPosition, wx.Size( 20,20 ), 0 )
		self.m_btnColourUp.Enable( False )

		bSizer18.Add( self.m_btnColourUp, 0, wx.ALL, 5 )

		self.m_btnColourDown = wx.Button( self.m_effectSettingsPanel, wx.ID_ANY, u"v", wx.DefaultPosition, wx.Size( 20,20 ), 0 )
		self.m_btnColourDown.Enable( False )

		bSizer18.Add( self.m_btnColourDown, 0, wx.ALL, 5 )


		bSizer16.Add( bSizer18, 0, wx.EXPAND, 5 )


		bSizer17.Add( bSizer16, 0, wx.ALIGN_CENTER_HORIZONTAL, 5 )


		fg_effectSettingsSizer.Add( bSizer17, 1, wx.EXPAND, 5 )

		self.m_lblColor = wx.StaticText( self.m_effectSettingsPanel, wx.ID_ANY, u"Change Color:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_lblColor.Wrap( -1 )

		fg_effectSettingsSizer.Add( self.m_lblColor, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5 )

		self.m_cpColor = wx.ColourPickerCtrl( self.m_effectSettingsPanel, wx.ID_ANY, wx.SystemSettings.GetColour( wx.SYS_COLOUR_3DLIGHT ), wx.DefaultPosition, wx.Size( 70,-1 ), wx.CLRP_DEFAULT_STYLE )
		self.m_cpColor.Enable( False )

		fg_effectSettingsSizer.Add( self.m_cpColor, 1, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL, 5 )


		self.m_effectSettingsPanel.SetSizer( fg_effectSettingsSizer )
		self.m_effectSettingsPanel.Layout()
		fg_effectSettingsSizer.Fit( self.m_effectSettingsPanel )
		bEffectSettingsSizer.Add( self.m_effectSettingsPanel, 0, wx.ALL, 5 )

		bEffectListSizer = wx.BoxSizer( wx.VERTICAL )

		self.m_lcEffectsList = wx.ListCtrl( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LC_REPORT|wx.LC_SINGLE_SEL )
		self.m_lcEffectsList.SetMinSize( wx.Size( 700,200 ) )

		bEffectListSizer.Add( self.m_lcEffectsList, 1, wx.ALL|wx.EXPAND, 5 )

		bAddRemoveSizer = wx.BoxSizer( wx.HORIZONTAL )

		self.m_btnAdd = wx.Button( self, wx.ID_ANY, u"Add", wx.DefaultPosition, wx.DefaultSize, 0 )
		bAddRemoveSizer.Add( self.m_btnAdd, 0, wx.ALL, 5 )

		self.m_btnRemove = wx.Button( self, wx.ID_ANY, u"Remove", wx.DefaultPosition, wx.DefaultSize, 0 )
		bAddRemoveSizer.Add( self.m_btnRemove, 0, wx.ALL, 5 )


		bEffectListSizer.Add( bAddRemoveSizer, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5 )


		bEffectSettingsSizer.Add( bEffectListSizer, 0, wx.EXPAND, 5 )

		bUpDownSizer = wx.BoxSizer( wx.VERTICAL )

		bUpDownSizer.SetMinSize( wx.Size( 100,-1 ) )
		self.m_btnUp = wx.Button( self, wx.ID_ANY, u"Move Up", wx.DefaultPosition, wx.DefaultSize, 0 )
		bUpDownSizer.Add( self.m_btnUp, 0, wx.ALL|wx.EXPAND, 5 )

		self.m_btnDown = wx.Button( self, wx.ID_ANY, u"Move Down", wx.DefaultPosition, wx.DefaultSize, 0 )
		bUpDownSizer.Add( self.m_btnDown, 0, wx.ALL|wx.EXPAND, 5 )


		bEffectSettingsSizer.Add( bUpDownSizer, 0, wx.ALIGN_CENTER_VERTICAL, 5 )


		bSettingsSizer.Add( bEffectSettingsSizer, 0, wx.ALL, 5 )

		bTextConfigSizer = wx.BoxSizer( wx.VERTICAL )

		self.m_txtSettings = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( -1,-1 ), wx.TE_DONTWRAP|wx.TE_MULTILINE )
		self.m_txtSettings.SetFont( wx.Font( wx.NORMAL_FONT.GetPointSize(), wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )
		self.m_txtSettings.SetMinSize( wx.Size( 1000,200 ) )

		bTextConfigSizer.Add( self.m_txtSettings, 0, wx.ALL, 5 )

		self.m_btnLoad = wx.Button( self, wx.ID_ANY, u"Load", wx.DefaultPosition, wx.DefaultSize, 0 )
		bTextConfigSizer.Add( self.m_btnLoad, 0, wx.ALL|wx.ALIGN_RIGHT, 5 )


		bSettingsSizer.Add( bTextConfigSizer, 1, 0, 5 )


		bSizer1.Add( bSettingsSizer, 1, wx.ALIGN_CENTER|wx.ALL, 5 )


		self.SetSizer( bSizer1 )
		self.Layout()
		self.m_timer = wx.Timer()
		self.m_timer.SetOwner( self, wx.ID_ANY )

		self.Centre( wx.BOTH )

		# Connect Events
		self.m_ledpanel.Bind( wx.EVT_PAINT, self.OnLedPanelPaint )
		self.m_ledpanel.Bind( wx.EVT_SIZE, self.OnLedPanelSize )
		self.m_spinLED.Bind( wx.EVT_SPINCTRL, self.OnLed_ctrl_changed )
		self.m_spinLED.Bind( wx.EVT_TEXT, self.OnLed_ctrl_changed )
		self.m_spinLED.Bind( wx.EVT_TEXT_ENTER, self.OnLed_ctrl_changed )
		self.m_cbLayout.Bind( wx.EVT_COMBOBOX, self.OnLayoutChanged )
		self.m_spinLines.Bind( wx.EVT_SPINCTRL, self.OnLayoutChanged )
		self.m_spinLines.Bind( wx.EVT_TEXT, self.OnLayoutChanged )
		self.m_spinLines.Bind( wx.EVT_TEXT_ENTER, self.OnLayoutChanged )
		self.m_spinDistance.Bind( wx.EVT_SPINCTRL, self.OnLayoutChanged )
		self.m_spinDistance.Bind( wx.EVT_TEXT, self.OnLayoutChanged )
		self.m_spinDistance.Bind( wx.EVT_TEXT_ENTER, self.OnLayoutChanged )
		self.m_cbActive.Bind( wx.EVT_CHECKBOX, self.OnEffectSettingChanged )
		self.m_cbEffect.Bind( wx.EVT_COMBOBOX, self.OnEffectSettingChanged )
		self.m_spinEffectRate.Bind( wx.EVT_SPINCTRLDOUBLE, self.OnEffectSettingChanged )
		self.m_spinEffectRate.Bind( wx.EVT_TEXT, self.OnEffectSettingChanged )
		self.m_spinEffectRate.Bind( wx.EVT_TEXT_ENTER, self.OnEffectSettingChanged )
		self.m_spinCutOff.Bind( wx.EVT_SPINCTRLDOUBLE, self.OnEffectSettingChanged )
		self.m_spinCutOff.Bind( wx.EVT_TEXT, self.OnEffectSettingChanged )
		self.m_spinCutOff.Bind( wx.EVT_TEXT_ENTER, self.OnEffectSettingChanged )
		self.m_cbBlending.Bind( wx.EVT_COMBOBOX, self.OnEffectSettingChanged )
		self.m_cbBlending.Bind( wx.EVT_TEXT_ENTER, self.OnEffectSettingChanged )
		self.m_lbPalette.Bind( wx.EVT_LISTBOX, self.OnEffectSettingChanged )
		self.m_lbPalette.Bind( wx.EVT_LISTBOX_DCLICK, self.OnPaletteDoubleClick )
		self.m_btnAddColour.Bind( wx.EVT_BUTTON, self.OnBtnAddColourClick )
		self.m_btnRemoveColour.Bind( wx.EVT_BUTTON, self.OnBtnRemoveColourClick )
		self.m_btnColourUp.Bind( wx.EVT_BUTTON, self.OnBtnColourUpClick )
		self.m_btnColourDown.Bind( wx.EVT_BUTTON, self.OnBtnColourDownClick )
		self.m_cpColor.Bind( wx.EVT_COLOURPICKER_CHANGED, self.OnColourChanged )
		self.m_lcEffectsList.Bind( wx.EVT_LIST_ITEM_DESELECTED, self.OnEffectsListItemSelected )
		self.m_lcEffectsList.Bind( wx.EVT_LIST_ITEM_SELECTED, self.OnEffectsListItemSelected )
		self.m_btnAdd.Bind( wx.EVT_BUTTON, self.OnBtnAddClicked )
		self.m_btnRemove.Bind( wx.EVT_BUTTON, self.OnBtnRemoveClicked )
		self.m_btnUp.Bind( wx.EVT_BUTTON, self.OnBtnUpClicked )
		self.m_btnDown.Bind( wx.EVT_BUTTON, self.OnBtnDownClicked )
		self.m_btnLoad.Bind( wx.EVT_BUTTON, self.OnApplyClicked )
		self.Bind( wx.EVT_TIMER, self.update, id=wx.ID_ANY )

	def __del__( self ):
		pass


	# Virtual event handlers, override them in your derived class
	def OnLedPanelPaint( self, event ):
		event.Skip()

	def OnLedPanelSize( self, event ):
		event.Skip()

	def OnLed_ctrl_changed( self, event ):
		event.Skip()



	def OnLayoutChanged( self, event ):
		event.Skip()







	def OnEffectSettingChanged( self, event ):
		event.Skip()











	def OnPaletteDoubleClick( self, event ):
		event.Skip()

	def OnBtnAddColourClick( self, event ):
		event.Skip()

	def OnBtnRemoveColourClick( self, event ):
		event.Skip()

	def OnBtnColourUpClick( self, event ):
		event.Skip()

	def OnBtnColourDownClick( self, event ):
		event.Skip()

	def OnColourChanged( self, event ):
		event.Skip()

	def OnEffectsListItemSelected( self, event ):
		event.Skip()


	def OnBtnAddClicked( self, event ):
		event.Skip()

	def OnBtnRemoveClicked( self, event ):
		event.Skip()

	def OnBtnUpClicked( self, event ):
		event.Skip()

	def OnBtnDownClicked( self, event ):
		event.Skip()

	def OnApplyClicked( self, event ):
		event.Skip()

	def update( self, event ):
		event.Skip()


