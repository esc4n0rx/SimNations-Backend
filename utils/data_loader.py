import json
import asyncio
from typing import Dict, List, Tuple
from sqlalchemy.orm import Session
from models.country import Country
from models.state import State
from config.database import get_db

class DataLoader:
    def __init__(self, json_file_path: str):
        self.json_file_path = json_file_path
        self._data_cache = None
        self._country_cache = {}
        self._state_cache = {}
    
    def load_json_data(self) -> Dict:
        """Load and cache JSON data"""
        if self._data_cache is None:
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                self._data_cache = json.load(f)
        return self._data_cache
    
    def populate_database(self, db: Session):
        """Populate database with countries and states from JSON"""
        data = self.load_json_data()
        
        for country_name, states_data in data.items():
            # Create or get country
            country = db.query(Country).filter(Country.name == country_name).first()
            if not country:
                country = Country(
                    name=country_name,
                    code=country_name[:3].upper()
                )
                db.add(country)
                db.flush()
            
            # Create states
            for state_name, traits in states_data.items():
                existing_state = db.query(State).filter(
                    State.name == state_name,
                    State.country_id == country.id
                ).first()
                
                if not existing_state:
                    state = State(
                        name=state_name,
                        country_id=country.id,
                        racionalidade=traits['racionalidade'],
                        conservadorismo=traits['conservadorismo'],
                        audacia=traits['audacia'],
                        autoridade=traits['autoridade'],
                        coletivismo=traits['coletivismo'],
                        influencia=traits['influencia']
                    )
                    db.add(state)
        
        db.commit()
    
    def get_optimized_state_data(self, db: Session) -> List[Tuple]:
        """Get optimized state data for matching algorithm"""
        if not self._state_cache:
            states = db.query(State).filter(State.is_occupied == False).all()
            self._state_cache = [
                (
                    state.id,
                    state.name,
                    state.country.name,
                    state.racionalidade,
                    state.conservadorismo,
                    state.audacia,
                    state.autoridade,
                    state.coletivismo,
                    state.influencia
                )
                for state in states
            ]
        return self._state_cache
    
    def invalidate_cache(self):
        """Invalidate cache when states are assigned"""
        self._state_cache = {}

# Global instance
data_loader = DataLoader('data/states_analysis.json')