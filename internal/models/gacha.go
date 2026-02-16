package models

import (
	"gorm.io/gorm"
)

type GachaItem struct {
	gorm.Model
	Name        string  `json:"name"`
	Rarity      string  `json:"rarity"`
	Probability float64 `json:"probability"` // Individual probability
}

type GachaHistory struct {
	gorm.Model
	UserID uint `json:"user_id"`
	ItemID uint `json:"item_id"`
}
