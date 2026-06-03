import typing
import aiohttp
import json
import hashlib
from typing import Dict, Set, Tuple, Optional, TypedDict

ROOT_HASH = 30791614295234051711832508548800469788824342480481074093233550318061354680202
TWENTY_HASH = 30791614295234051711832508548800469788824342480481074093233550318061354680202 

# For convenience in typing, we define several type aliases
type Sender = typing.Callable[[dict],typing.Awaitable[None]]

class Change(typing.TypedDict):
    old: int
    src: str
    dst: str
    n: int
    memo: str

class Block(typing.TypedDict):
    change: Change
    signature: int

class BlockProMax(typing.TypedDict):
    block: Block
    depth: int
    balances: Dict[str, int] # account name to account balance
    paid: Set[Tuple[str,str]] # account name to booths it's paid for

class UserData(typing.TypedDict, total=False):
    key: int
    host: str

class BlockChain:

    def check_paid(self, acc: str, booth: str) -> bool:
        head_block_pro_max = self.pointers.get(self.head_hash)
        ledger = head_block_pro_max["paid"]
        paid = (acc, booth) in ledger
        return paid

    def valid(self, src: str, dst: str, n: int) -> bool:
        if src not in self.users or dst not in self.users:
            return False
        if src.endswith("_b"): # src is a booth, dst must be a player
            if dst.endswith("_b"):
                return False
            if src[:-2] == dst:
                return False
            if not (0 <= n <= 10):
                return False
            if not self.check_paid(dst, src):
                return False
        if dst.endswith("_b"): # dst is a booth, src must be a player
            if src.endswith("_b"):
                return False
            if dst[:-2] == src:
                return False
            if not (1 <= n <= 5):
                return False
        return True

    def sign(self, value: Change, private_key: int, public_key: int) -> None:
        hash = self.hash(value)
        return pow(hash, private_key, public_key)

    def check_signature(self, value: Change, public_key: int, signature: int) -> None:
        hash = self.hash(value)
        valid = (hash == pow(signature, 0x10001, public_key))
        return valid

    def hash(self, change: Change) -> int:
        string_val = json.dumps(change, separators=(',',':'), indent=None, sort_keys=True, ensure_ascii=False)
        byte_string = string_val.encode('utf-8')
        hash_bytes = hashlib.sha256(byte_string).digest()
        hash_int = int.from_bytes(hash_bytes, byteorder='big')
        return hash_int

    def __init__(self):
        """Initialize a blockchain with no blocks in it."""
        self.root = ROOT_HASH
        self.head_hash = self.root
        sentinel_block: BlockProMax = {
            "block": None,
            "depth": 0,
            "balances": {},
            "paid": set()
        }
        self.unfinished_blocks = {}
        self.pointers = {self.head_hash: sentinel_block} # hash key block pro max value
        self.users = {} # acc name : public key 
    
    def add_users(self, userdata: dict[str,UserData]) -> None:
        """Add users to the set known by the BlockChain.
        userdata will be a dict with the following properties:
        
        - keys are user account names
        - values are dicts which may have several keys, including
            - "key": a large int which is this agent's public key
        """
        for name, userdatum in userdata.items():
            self.users[name] = userdatum["key"]

    def create_block(self, src:str, dst:str, n:int, memo:str, privkey:int) -> Block|str:
        """Create a block that would apply the given delta to the current head;
        if this cannot be done for some reason, return that reason as a string.
        Include the following strings:
        
        - 'Unknown user: «username»' if the src or dst not previously added as a user
        - 'Not authorized' if this is not a booth-to-player or player-to-booth transfer
        - 'Not authorized' if this is is a self-transfer
        - 'Invalid amount' if n is not a permitted integer
        - 'Not paid` if src is a booth and the player isn't in a paid state
        - 'Wrong key' if the privkey does not match the pubkey of the src account
        
        If multiple messages might be returned, any one of them may be returned.
        """
        change: Change = {
            "old": self.head_hash,
            "src": src,
            "dst": dst,
            "n": n,
            "memo": memo
        }
        block: Block = {
            "change": change,
            "signature": self.sign(change, privkey, self.users[change["src"]])
        }

        old_hash = self.head_hash
        old_bpm = self.pointers[old_hash]

        if src not in self.users:
            return "Unknown user: " + src
        if dst not in self.users:
            return "Unknown user: " + dst
        if src.endswith("_b"): # src is a booth, dst must be a player
            if dst.endswith("_b"):
                return "Not authorized"
            if src[:-2] == dst:
                print("USers")
                print(src[:-2])
                print(dst)
                print("-----")
                return "Not authorized"
            if not (0 <= n <= 10):
                return "Invalid amount"
            if not self.check_paid(dst, src):
                return "Not paid"
        elif dst.endswith("_b"): # dst is a booth, src must be a player
            if src.endswith("_b"):
                return "Not authorized"
            if dst[:-2] == src:
                return "Not authorized"
            if not (1 <= n <= 5):
                return "Invalid amount"
        else:
            return "Not authorized"
        
        src_pubkey = self.users.get(change["src"])
        if src_pubkey is None:
            return "Wrong key"
        if not self.check_signature(change, src_pubkey, block["signature"]):
            return "Wrong key"
        
        # balances = dict.fromkeys(self.users, 20)

        # balances.update(old_block["balances"])
        # paid = set(old_block["paid"])

        # balances[change["src"]] -= change["n"]
        # balances[change["dst"]] += change["n"]

        # if change["dst"].endswith("_b"): # (player, booth)
        #     paid.add((change["src"], change["dst"]))
        # if change["src"].endswith("_b") and (change["dst"], change["src"]) in paid:
        #     paid.remove((change["dst"], change["src"]))

        # bpm: BlockProMax = {
        #     "block": block,
        #     "balances": balances,
        #     "paid": paid,
        #     "depth": old_block["depth"] + 1
        # }
        
        # hash = self.hash(block["change"])
        # self.pointers[hash] = bpm

        # if bpm["depth"] > self.pointers[self.head_hash]["depth"]:
        #     print("Old head hash depth:" + str(self.pointers[self.head_hash]["depth"]))
        #     print("New head hash depth:" + str(bpm["depth"]))
        #     self.head_hash = hash
        # elif bpm["depth"] == self.pointers[self.head_hash]["depth"] and hash < self.head_hash:
        #     self.head_hash = hash
        return block

        
        
        
    async def add_block(self, block: Block, send_json: Sender) -> None:
        """Add a block to the blockchain if it is valid.
        If it is invalid, ignore it.
        If it depends on a missing old value, request that through passed-in `send_json`
        and keep track of the unfinished block.
        
        If there are unfinished blocks that can be finished after adding this one,
        also add (or unverify and discard) those.
        """

        dependencies = [block]

        while dependencies:
            dependent = dependencies.pop(0)
            

            change = dependent["change"]
            old_hash = change["old"]
    
            if old_hash not in self.pointers:
                await send_json({"missing": old_hash})
                if old_hash not in self.unfinished_blocks:
                    self.unfinished_blocks[old_hash] = []
                self.unfinished_blocks[old_hash].append(dependent)
                return
            
            old_block = self.pointers[change["old"]]

            src_pubkey = self.users.get(change["src"])
            if src_pubkey is None:
                return
            if not self.check_signature(change, src_pubkey, dependent["signature"]):
                return

            if self.valid(dependent["change"]["src"], dependent["change"]["dst"], dependent["change"]["n"]):

                
                
                balances = dict.fromkeys(self.users, 20)

                balances.update(old_block["balances"])
                paid = set(old_block["paid"])

                balances[change["src"]] -= change["n"]
                balances[change["dst"]] += change["n"]

                if change["dst"].endswith("_b"): # (player, booth)
                    paid.add((change["src"], change["dst"]))
                if change["src"].endswith("_b") and (change["dst"], change["src"]) in paid:
                    paid.remove((change["dst"], change["src"]))

                bpm: BlockProMax = {
                    "block": dependent,
                    "balances": balances,
                    "paid": paid,
                    "depth": old_block["depth"] + 1
                }
                
                hash = self.hash(dependent["change"])
                self.pointers[hash] = bpm

                if bpm["depth"] > self.pointers[self.head_hash]["depth"]:
                    print("Old head hash depth:" + str(self.pointers[self.head_hash]["depth"]))
                    print("New head hash depth:" + str(bpm["depth"]))
                    self.head_hash = hash
                elif bpm["depth"] == self.pointers[self.head_hash]["depth"] and hash < self.head_hash:
                    self.head_hash = hash
                if hash in self.unfinished_blocks:
                    dependencies.extend(self.unfinished_blocks[hash])




    def get_head_hash(self) -> int:
        """Returns the hash of the current head of the blockchain"""
        return self.head_hash

    def get_accounts(self) -> dict[str,int]:
        """Return the ticket count of each user in the current head of the blockchain.
        If the count of a "user" is 20 (the starting amount), the function can either 
        include "user":20 or omit the "user" entry entirely (which one is implementation defined).
        """
        accounts = {}
        balances = self.pointers[self.head_hash]["balances"]
        for account, balance in balances.items():
            accounts[account] = balance
        return accounts

    def get_chain(self) -> dict[int, Block]:
        """Return all the blocks that have been added to this blockchain.
        Returns a dict where keys are the hash of each block's change
        and values are block objects.
        """
        chain = {}
        for hash_val, bpm in self.pointers.items():
            if not hash_val == ROOT_HASH:
                chain[hash_val] = bpm["block"]
        return chain

    def get_block(self, blockid: int) -> Block|None:
        """Given the hash of the change of a block,
        return that block if it is present in the BlockChain.
        Should be equivalent to self.get_chain().get(blockid),
        but ideally faster and/or a smaller return value.
        """
        if blockid not in self.pointers:
            return None
        bpm = self.pointers.get(blockid)
        print(bpm["block"])
        return bpm["block"]

    def is_live(self, blockid: int) -> bool:
        """Given the hash of a block's change,
        return True iff the block is on the path from the head to the root.
        We recommend optimizing for the case where the chain has millions of blocks,
        the block *is* on that path, and the block is close to the head.
        """
        # The staff-provided code works, but if you can make it faster based on your datastructures and internal implementation, please do so; this method is called at least once per game played and we expect the total number of blocks to reach the hundreds of thousands
        if self.get_block(blockid) is None: return False
        ptr = self.get_head_hash()
        while ptr != ROOT_HASH:
            if ptr == blockid: return True
            ptr = self.get_block(ptr)['change']['old']
        return False

