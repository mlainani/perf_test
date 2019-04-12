#!/bin/sh

sleepInt=0
ROOT=0

value=`ImProvHelper.sh --ReadLid ILID_INSTRUMENTDATA_INSTRUMENT_MODEL_TYPE`
case "$value" in
*ROOT*)
	ROOT=1
    sleepInt=21
    ;;
*)
    sleepInt=10
    ;;
esac

# NET status is checked multiple times to be sure it remains synced. CAM3 has an issue.
# Its gets SYCnEt and then goes to NOSYC. The sleep time is reduced after the first attempt
for i in 1 2 3; do
	echo "***** Checking NET-Status: Attempt[$i/3] Intv : $sleepInt sec"
	while true; do
	    STATUS=`pib -gdn .mas.status.f0_core.NetRegisteredFlag`   
	    if [ "$STATUS" == "1" ] ; then
	    	sleep $sleepInt    	
			break
	    fi
	    sleep $sleepInt;
	done

	if [ "$ROOT" == "1" ];then
		sleepInt=$(( sleepInt-10 ))
	else
		sleepInt=5
	fi
done

# Once system is SYCnEt, we make configurations

# macSIFS in ms
pib -sdn .rf_mac.static_config.chan_mgr.macSIFS -v 2

# RTS Threshold in usec
pib -sdn .rf_mac.static_config.chan_mgr.macRTSThreshold -v 300000

# macShortTxDCmax
pib -sdn .rf_mac.static_config.chan_mgr.macShortTxDCmax -v 4000

#enable actda: enabling actda will overwrite AIFS, CW
pib -sdn .rf_mac.static_config.chan_mgr.enable_actda -v 1

# configure the IPv6 address and routes
if [ "$ROOT" == "1" ];then
	# configuration for ROOT
	/sbin/ip -6 route add bbbb::1 via aaaa::2
else
	# configuration for node
	/sbin/ip addr add bbbb::2/64 dev usb0
fi

echo ""
echo "############################################"
echo "##                                        ##"
echo "##       JAPAN Configuration Loaded       ##"
echo "##                 READY                  ##"
echo "##                                        ##"
echo "############################################"
echo ""


