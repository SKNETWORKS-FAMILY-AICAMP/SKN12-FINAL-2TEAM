from .data_table import DataRow

class ItemData(DataRow):
    """아이템 데이터 모델 (테스트용)"""
    
    def __init__(self):
        self.id: int = 0
        self.name: str = ""
        self.type: str = ""
        self.level: int = 0
        self.price: int = 0
        self.description: str = ""
        
    def from_dict(self, data: dict):
        """딕셔너리에서 객체로 변환"""
        self.id = int(data.get('id', 0))
        self.name = data.get('name', '')
        self.type = data.get('type', '')
        self.level = int(data.get('level', 0))
        self.price = int(data.get('price', 0))
        self.description = data.get('description', '')
        
    def __repr__(self):
        return f"ItemData(id={self.id}, name='{self.name}', type='{self.type}', level={self.level})"