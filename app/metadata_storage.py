## Purpose: stores all the changes made to portfolios on the dashboard

## base imports
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List


class MetadataStorage:
    ## Saved format (by ID as a string):

    ## ID: string
    ## Stocks: dict (symbol, weight)
    ## Creation time: date/time
    ## Modification time: date/time
    ## Modifications: max history of 5 (timestamp and portfolio)
    ## Num Changes: int

    def __init__(self, pathway = "data/portfolio_metadata.json"):

        ## find portfolio specific path
        self.pathway = Path(pathway)
        self.pathway.parent.mkdir(exist_ok = True)

        ## create new path if it doesnt already exist
        if not self.pathway.exists():
            self.save_data({})


    
    def load_data(self) -> Dict:
        ## loading a stored metadata file
        with open(self.pathway, 'r') as f:
            return json.load(f)
        
    
    def save_data(self, data: Dict):
        ## saves metadata to its own file
        with open(self.pathway, 'w') as f:
            json.dump(data, f, default = str)

    
    def save_portfolio(self, port_id: str, stocks: List[Dict]):
        data = self.load_data()

        # Filter out stocks that have no weight
        stocks = [s for s in stocks if s['weight'] > 0]

        ## check if portfolio already exists
        is_new = port_id not in data

        ## package metadata
        data[port_id] = {
            'stocks': stocks,
            'c_time': datetime.now().isoformat() if is_new else data[port_id]['c_time'],
            'm_time': datetime.now().isoformat(),
            'num_changes': 0 if is_new else data[port_id]['num_changes'] + 1,
            'mods': [] if is_new else data[port_id]['mods']
        }

        data[port_id]['mods'].insert(0,{
            'time': datetime.now().isoformat(),
            'port': stocks})
        
        if len(data[port_id]['mods']) > 5:
            data[port_id]['mods'] = data[port_id]['mods'][:5]


        self.save_data(data)
        return data[port_id]
    
    def get_portfolio(self, port_id: str):
        ## loads a portfolio by id
        data = self.load_data()
        return data.get(port_id)
    
    def get_port_weights(self, port_id: str):
        ## loads just a portfolio's stock weights
        rc = None

        data = self.load_data()
        if port_id in data:
            rc = data[port_id]['stocks']
        
        return rc

    
    def get_history(self, port_id: str):
        ## lists out the 5 most recent modifications for a portfolios 
        rc = None
        data = self.load_data()
        if port_id in data and 'mods' in data[port_id]:
            rc = data[port_id]['mods'] 
        
        return rc
        

    def list_ports(self) -> List[Dict]:
        ## lists all the currently saved portfolios
        data = self.load_data()

        portfolios = []
        for port_id, info in data.items():
            portfolios.append({'port_id': port_id, **info})

        return portfolios


    def delete_port(self, port_id: str) -> bool:
        ## deletes port_id's associated metadata

        data = self.load_data()
        rc = port_id in data

        if rc:
            del data[port_id]
            self.save_data(data)
        
        return rc