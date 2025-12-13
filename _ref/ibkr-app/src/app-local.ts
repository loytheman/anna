import config from "./helpers/config.ts";
import { IBApi, EventName, ErrorCode, type Contract } from "@stoqey/ib";
import { AccountSummary } from  "@stoqey/ibkr";



// create IBApi object
console.log(config);

const ib = new IBApi({
  clientId: config.ib.clientId,
  host: config.ib.host,
  port: config.ib.port,
});

// register event handler

let positionsCount = 0;

ib.on(EventName.error, (err: Error, code: ErrorCode, reqId: number) => {
  console.error(`${err.message} - code: ${code} - reqId: ${reqId}`);
})
  .on(
    EventName.position,
    (account: string, contract: Contract, pos: number, avgCost?: number) => {
      console.log(`${account}: ${pos} x ${contract.symbol} @ ${avgCost}`);
      positionsCount++;
    },
  )
  .once(EventName.positionEnd, () => {
    console.log(`Total: ${positionsCount} positions.`);
    ib.disconnect();
  });



export const run = async () => {
    
    const accountSummary = await AccountSummary.Instance;
    const accountType  = accountSummary.accountSummary.AccountType;

    console.log(accountType, "Account Type");
};


ib.connect();
ib.reqPositions();
run();

