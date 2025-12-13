import ibkr, { AccountSummary } from "@stoqey/ibkr";

export const run = async () => {
    await ibkr();
    const accountSummary = await AccountSummary.Instance;
    const accountType  = accountSummary.accountSummary.AccountType;

    console.log(accountType, "Account Type");
};

run();