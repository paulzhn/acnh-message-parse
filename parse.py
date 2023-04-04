from pymsyt import Msbt
import pymsyt


data = open("BO_ApproachA_Always.msbt", "rb").read()
msbt = Msbt.from_binary(data)
msyt_text = msbt.to_yaml() # Convert MSBT to MSYT YAML
json_text = msbt.to_json() # Convert MSBT to JSON
msbt_dict = msbt.to_dict() # Convert to an editable Python dictionary
# for entry, contents in msbt_dict["entries"].items() # Iterate MSBT text entries
#     print(f"{entry} = {contents}")
# msbt_dict["entries"]["Armor_999_Head"] = { # Adding a new text entry
#     "contents": [{"text":"Some new helmet"}]
# }
# open("ArmorHead.msbt", "wb").write( # Saving modified file
#     Msbt.from_dict(msbt_dict).to_binary(big_endian=True)
# )

print(json_text)

