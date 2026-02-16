package services

import (
	"errors"
	"gacha-system/internal/models"
	"math/rand"

	"gorm.io/gorm"
)

const GachaCost = 300

type GachaService struct {
	db *gorm.DB
}

func NewGachaService(db *gorm.DB) *GachaService {
	return &GachaService{db: db}
}

// InitializeGachaItems creates sample gacha items if they don't exist
func (s *GachaService) InitializeGachaItems() error {
	var count int64
	s.db.Model(&models.GachaItem{}).Count(&count)
	if count > 0 {
		return nil
	}

	items := []models.GachaItem{
		{Name: "Wooden Sword", Rarity: "N", Probability: 0.5},
		{Name: "Iron Sword", Rarity: "R", Probability: 0.3},
		{Name: "Steel Sword", Rarity: "SR", Probability: 0.15},
		{Name: "Diamond Sword", Rarity: "SSR", Probability: 0.05},
	}

	return s.db.Create(&items).Error
}

func (s *GachaService) DrawGacha(userID uint) (*models.GachaItem, error) {
	var selectedItem *models.GachaItem

	err := s.db.Transaction(func(tx *gorm.DB) error {
		// 1. Check user gem balance
		var user models.User
		if err := tx.First(&user, userID).Error; err != nil {
			return err
		}

		if user.Gem < GachaCost {
			return errors.New("insufficient gems")
		}

		// 2. Get all gacha items
		var items []models.GachaItem
		if err := tx.Find(&items).Error; err != nil {
			return err
		}

		if len(items) == 0 {
			return errors.New("no gacha items available")
		}

		// 3. Calculate total probability
		var totalProbability float64
		for _, item := range items {
			totalProbability += item.Probability
		}

		// 4. Generate random number
		// Go 1.20+ automatically seeds the global random source.
		target := rand.Float64() * totalProbability

		// 5. Select item
		var currentProbability float64
		for _, item := range items {
			currentProbability += item.Probability
			if target <= currentProbability {
				selectedItem = &item
				break
			}
		}

		if selectedItem == nil {
			// Fallback
			selectedItem = &items[len(items)-1]
		}

		// 6. Deduct gems
		user.Gem -= GachaCost
		if err := tx.Save(&user).Error; err != nil {
			return err
		}

		// 7. Save history
		history := models.GachaHistory{
			UserID: userID,
			ItemID: selectedItem.ID,
		}
		if err := tx.Create(&history).Error; err != nil {
			return err
		}

		return nil
	})

	if err != nil {
		return nil, err
	}

	return selectedItem, nil
}
