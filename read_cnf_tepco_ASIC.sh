#!/bin/sh

#device Type
echo -e "~~~~~ LIDs ~~~~~"
value=`eval ImProvHelper.sh --ReadLid ILID_INSTRUMENTDATA_INSTRUMENT_MODEL_TYPE`
echo -e "ILID_INSTRUMENTDATA_INSTRUMENT_MODEL_TYPE $value"

value=`eval ImProvHelper.sh --ReadLid ILID_NGC_USB_DEV_OWN_MAC_ADDRESS`
echo -e "ILID_NGC_USB_DEV_OWN_MAC_ADDRESS $value"

value=`eval ImProvHelper.sh --ReadLid ILID_NGC_USB_HOST_CGR_MAC_ADDRESS`
echo -e "ILID_NGC_USB_HOST_CGR_MAC_ADDRESS $value"

value=`eval ImProvHelper.sh --ReadLid ILID_ACT_NAC_MODE`
echo -e "ILID_ACT_NAC_MODE $value"

value=`eval ImProvHelper.sh --ReadLid ILID_ACT_ENABLE_6LOWPAN_HC`
if [ "$value" == "2" ]
then
 valStr="compressed"
else
 valStr="uncompressed"
fi
echo -e "ILID_ACT_ENABLE_6LOWPAN_HC $value ($valStr)"

value=`eval ImProvHelper.sh --ReadLid ILID_ACT_MAS_DISABLEMAC`
echo -e "ILID_ACT_MAS_DISABLEMAC $value"

# #added by Nikeshman for tableTop setup

# #Star Topology
value=`eval ImProvHelper.sh --ReadLid ILID_ACT_NETWORK_TOPOLOGY_CONFIG`
if [ "$value" == "0" ]
then
 valStr="MESH"
else
 valStr="STAR"
fi
echo -e "ILID_ACT_NETWORK_TOPOLOGY_CONFIG $value ($valStr)"

# #SSID
value=`eval ImProvHelper.sh --ReadLid ILID_NGC_MAS_SSID`
echo -e "ILID_NGC_MAS_SSID $value"


# #Start Frequency
value=`eval ImProvHelper.sh --ReadLid ILID_NGC_RFPHY_START_FREQ`
echo -e "ILID_NGC_RFPHY_START_FREQ $value KHz"

# #Channel Mask
value=`eval ImProvHelper.sh --ReadLid ILID_ACT_RFPHY_CHANNEL_MASK`

value2=`eval pib -gdn .rf_mac.dynamic_config.sync_mgr.numOfChannels`
echo -e "ILID_ACT_RFPHY_CHANNEL_MASK $value ($value2 channels)"

# #Channel Spacing
value=`eval ImProvHelper.sh --ReadLid ILID_NGC_RFPHY_CH_SPACING`
echo -e "ILID_NGC_RFPHY_CH_SPACING $value KHz"

# #Frame Error Check
value=`eval ImProvHelper.sh --ReadLid ILID_NGC_RFPHY_FSK_FEC`
echo -e "ILID_NGC_RFPHY_FSK_FEC $value"

#TX Power
value=`eval ImProvHelper.sh --ReadLid ILID_ACT_MAX_TX_PWR`
echo -e "ILID_ACT_MAX_TX_PWR $value dBm"

value=`eval ImProvHelper.sh --ReadLid ILID_ACT_MAX_TX_PWR_ADJUST`
echo -e "ILID_ACT_MAX_TX_PWR_ADJUST $value/2 dB"

value=`eval ImProvHelper.sh --ReadLid ILID_NGC_RFMAC_REGULATION_MAX_DUTY_CYCLE`
echo -e "ILID_NGC_RFMAC_REGULATION_MAX_DUTY_CYCLE $value msec"

value=`eval ImProvHelper.sh --ReadLid ILID_NGC_RFMAC_REGULATION_DUTY_CYCLE_DURATION`
echo -e "ILID_NGC_RFMAC_REGULATION_DUTY_CYCLE_DURATION $value sec"

value=`eval ImProvHelper.sh --ReadLid ILID_NGC_MAS_DUTYCYCLELIMIT_PSU`
echo -e "ILID_NGC_MAS_DUTYCYCLELIMIT_PSU $value sec"


echo -e "~~~~~ PIBs ~~~~~"

# enable_actda
value=`eval pib -gdn .rf_mac.static_config.chan_mgr.enable_actda `
echo -e "enable_actda \t= $value"
# macSIFS
value=`eval pib -gdn .rf_mac.static_config.chan_mgr.macSIFS`
echo -e "macSIFS \t= $value msec"
# macAIFS
value=`eval pib -gn .rf_mac.static_config.chan_mgr.macAIFS`
value2="${value:16:8}"
printf "macAIFS \t= 0x%s (%dms)\n" $value 0x$value2
# macMinCW
value=`eval pib -gn .rf_mac.static_config.chan_mgr.macMinCW`
value2="${value:16:8}"
printf "macMinCW \t= 0x%s (%d)\n" $value 0x$value2
# macMaxCW
value=`eval pib -gn .rf_mac.static_config.chan_mgr.macMaxCW`
value2="${value:16:8}"
printf "macMaxCW \t= 0x%s (%d)\n" $value 0x$value2

# macMinCW_root 
value=`eval pib -gn .rf_mac.static_config.chan_mgr.macMinCW_root `
value2="${value:16:8}"
printf "macMinCW_root \t= 0x%s (%d)\n" $value 0x$value2

# macMaxCW_root 
value=`eval pib -gn .rf_mac.static_config.chan_mgr.macMaxCW_root `
value2="${value:16:8}"
printf "macMaxCW_root \t= 0x%s (%d)\n" $value 0x$value2

# macRTSThreshold
value=`eval pib -gdn .rf_mac.static_config.chan_mgr.macRTSThreshold`
echo -e "macRTSThreshold \t= $value usec"
# forceTxModulation
# FSK_75: 0x08, OFDM_200: 0x43, OFDM_600: 0x46, LR: 0x81
value=`eval pib -gn .rf_mac.static_config.pkt_mgr.forceTxModulation`
if [ "$value" == "46" ]
then
 valStr="OFDM_600"
elif [ "$value" == "43" ]
then
 valStr="OFDM_200"
elif [ "$value" == "36" ]
then
 valStr="OFDM_1200"
elif [ "$value" == "08" ]
then
 valStr="FSK_75"
elif [ "$value" == "81" ]
then
 valStr="LONG_RANGE"
elif [ "$value" == "00" ]
then
 valStr="NOT SET"
else
 valStr="UNDEF"
fi
echo -e "forceTxModulation \t= 0x$value ($valStr)"
# macShortTxDCmax
value=`eval pib -gdn .rf_mac.static_config.chan_mgr.macShortTxDCmax`
echo -e "macShortTxDCmax \t= $value msec"
# macRegulationTxDCmax
value=`eval pib -gdn .rf_mac.static_config.chan_mgr.macRegulationTxDCmax`
echo -e "macRegulationTxDCmax \t= $value msec"
# macRegulationTxDCduration
value=`eval pib -gdn .rf_mac.static_config.chan_mgr.macRegulationTxDCduration`
echo -e "macRegulationTxDCduration \t= $value sec"
# DutyCycleLimitSecPerHour
value=`eval pib -gdn .mas.static_config.f0_core.DutyCycleLimitSecPerHour`
echo -e "DutyCycleLimitSecPerHour \t= $value sec/hour"
#current accumulated TXtime
value=`eval pib -gdn .mas.status.f0_core.TxTimeAcc1hRf`
echo -e "Current TxTimeAcc1hRf \t= $value msec"

# macUnitBackoffPeriod
value=`eval pib -gdn .rf_mac.static_config.chan_mgr.macUnitBackoffPeriod`
echo -e "macUnitBackoffPeriod \t= $value msec"
# macAlwaysBO
value=`eval pib -gdn .rf_mac.static_config.chan_mgr.macAlwaysBO`
echo -e "macAlwaysBO \t\t= $value (first Packet on quiet channel)"
# disable_ack_request
value=`eval pib -gdn .rf_mac.static_config.chan_mgr.disable_ack_request`
echo -e "disable_ack_request \t= $value"

