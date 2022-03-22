import json
import time
import contract as c
import cyclemanager as cmanager
from datetime import datetime,timedelta
import time
import json

dm_contract_addr = "0xE2D26507981A4dAaaA8040bae1846C14E0Fb56bF"
loop_sleep_seconds = 2
start_polling_threshold_in_seconds = 0

# load private key
wallet_private_key = open('key.txt', "r").readline()

# load public address
wallet_public_addr = open('pa.txt', "r").readline().strip().strip('\'').strip('\"').strip()

# load abi
f = open('bakedbeans_abi.json')
dm_abi = json.load(f)

# create contract
dm_contract = c.connect_to_contract(dm_contract_addr, dm_abi)

cycle = cmanager.build_cycle_from_config()
nextCycleId = 1

# methods
def rebake():
    txn = dm_contract.functions.hatchEggs(wallet_public_addr).buildTransaction(c.get_tx_options(wallet_public_addr, 500000))
    return c.send_txn(txn, wallet_private_key)

def eat():
    txn = dm_contract.functions.sellEggs().buildTransaction(c.get_tx_options(wallet_public_addr, 500000))
    return c.send_txn(txn, wallet_private_key)

def my_beans():
    total = dm_contract.functions.getMyMiners(wallet_public_addr).call()
    return total

def payout_to_rebake():
    total = dm_contract.functions.beanRewards(wallet_public_addr).call()
    return total/1000000000000000000

def buildTimer(t):
    mins, secs = divmod(int(t), 60)
    hours, mins = divmod(int(mins), 60)
    timer = '{:02d} hours, {:02d} minutes, {:02d} seconds'.format(hours, mins, secs)
    return timer

def countdown(t):
    while t:
        print(f"Next poll in: {buildTimer(t)}", end="\r")
        time.sleep(1)
        t -= 1

def findCycleMinimumBnb(cycleId):
    for x in cycle:
        if x.id == cycleId:
            return x.minimumBnb
            break
        else:
            x = None

def findCycleType(cycleId):
    for x in cycle:
        if x.id == cycleId:
            return x.type
            break
        else:
            x = None

def findCycleEndTimerAt(cycleId):
    for x in cycle:
        if x.id == cycleId:
            return x.endTimerAt
            break
        else:
            x = None

def getNextCycleId(currentCycleId):
    cycleLength = len(cycle)
    if currentCycleId == cycleLength:
        return 1
    else:
        newCycleId = currentCycleId + 1
        return newCycleId

def seconds_until_cycle(endTimerAt):
    time_delta = datetime.combine(
        datetime.now().date(), datetime.strptime(endTimerAt, "%H:%M").time()
    ) - datetime.now()
    return time_delta.seconds

# create infinate loop that checks contract every set sleep time
nextCycleType = findCycleType(nextCycleId)
def itterate(nextCycleId, nextCycleType):
    cycleMinimumBnb = findCycleMinimumBnb(nextCycleId)
    secondsUntilCycle = seconds_until_cycle(findCycleEndTimerAt(nextCycleId))
    myBeans = my_beans()
    payoutToRebake = payout_to_rebake()

    dateTimeObj = datetime.now()
    timestampStr = dateTimeObj.strftime("[%d-%b-%Y (%H:%M:%S)]")

    sleep = loop_sleep_seconds 
    
    print("********** Baked Beans *******")
    print(f"{timestampStr} Next cycle type: {nextCycleType}")
    print(f"{timestampStr} My beans: {myBeans} beans")
    print(f"{timestampStr} Estimated daily beans: {myBeans*0.08:.3f}")
    print(f"{timestampStr} Payout available for rebake/eat: {payoutToRebake:.8f} BNB")
    print(f"{timestampStr} Minimum set for rebake/eat: {cycleMinimumBnb:.8f} BNB")
    print("******************************")

    if secondsUntilCycle > start_polling_threshold_in_seconds:
        sleep = secondsUntilCycle - start_polling_threshold_in_seconds

    countdown(int(sleep))

    payoutToRebake = payout_to_rebake()

    if payoutToRebake >= cycleMinimumBnb:
        if nextCycleType == "rebake":
            rebake()
        if nextCycleType == "eat":
            eat()
        
        if nextCycleType == "rebake":
            print("********** REBAKED *******")
            print(f"{timestampStr} Rebaked {payoutToRebake:.8f} BNB to the pool!")
        if nextCycleType == "eat":
            print("********** ATE ***********")
            print(f"{timestampStr} Ate {payoutToRebake:.8f} BNB!")

        internalNextCycleId = getNextCycleId(nextCycleId)
        internalNextCycleType = findCycleType(internalNextCycleId)
        print(f"{timestampStr} Next cycleId is: {internalNextCycleId}")
        print(f"{timestampStr} Next cycle type will be: {internalNextCycleType}")
        print("**************************")

        print(f"{timestampStr} Sleeping for 1 min until next cycle starts..")
        countdown(60)

        return internalNextCycleId, internalNextCycleType
 

retryCount = 0
while True:
    try: 
        if retryCount < 5:
            result = itterate(nextCycleId, nextCycleType)
            nextCycleId = result[0]
            nextCycleType = result[1]
    except Exception as e:
        print("[EXCEPTION] Something went wrong! Message:")
        print(f"[EXCEPTION] {e}")
        retryCount = retryCount + 1
        if retryCount < 5:
            itterate(nextCycleId, nextCycleType)
        print(f"[EXCEPTION] Retrying! (retryCount: {retryCount})")
