# Rules and Guidelines

- Teams can have up to 4 members.
- You can use the functions and variables we provide, but attempting to access any private variables or functions of the game not provided by us will result in the disqualification of your team.
- **Only one Global variable** is **ALLOWED** (`memory`). If you feel your use of global variables does not maintain state, consult your mentor to see if it is allowed.
- You cannot use any of the following libraries/modules: `os` ,`subprocess` and other libraries that can run commands.
- You can change `a.py` and `b.py` files.
- Collaborating with other teams is allowed. There will be no plagiarism check either, but it's up to you whether you want to help your opponent!
- Ensure `memory` does not exceed the allowed length of 100. If `memory` exceeds this limit at any point during the match, that team will **instantly lose**.
- If the team **meets all conditions**, it **passes validation**. Otherwise, it fails and loses the match.

- Each team must submit only one script by __ March, 2026. No submissions or modifications will be accepted after this deadline.
    - Note: The deadline will be updated soon. Stay tuned!

## Game End Conditions

- Each match runs for a fixed duration with 6 teams competing.
- When the timer ends, the **team with the most kills wins**.
- If two or more teams have the **same number of kills**, tie-breaker conditions apply:
    - The team with **fewer deaths** wins.
    - If both kills and deaths are equal, the match ends with multiple winners.
    

### **🔴 Common Mistakes That Will Fail Validation**

| Mistake | Reason |
| --- | --- |
| Missing **`team_name`**, **`troops`**, **`deploy_list`**, or **`team_signal`** | All four variables **must** exist. |
| `troops` has **less/more than 8** elements | `troops` **must** contain **exactly** 8 troop types. |
| `troops` has **duplicate troop types** | The **8 troops must be unique**. |
| `team_signal` is **longer than `SIGNAL_LENGTH`** | The signal must be **shorter than the limit**. |
| `Deploy` or `Utils` **is missing** | These classes must be **present in the script**. |
| Class `My` is created by me and used in the script. | Any other class other than Deploy or Utils is not allowed. |