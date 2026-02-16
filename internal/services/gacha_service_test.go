package services

import (
	"gacha-system/internal/models"
	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
	"testing"
)

func TestGachaProbability(t *testing.T) {
	// Setup in-memory database
	db, err := gorm.Open(sqlite.Open("file::memory:?cache=shared"), &gorm.Config{})
	if err != nil {
		t.Fatalf("failed to connect database: %v", err)
	}

	db.AutoMigrate(&models.User{}, &models.GachaItem{}, &models.GachaHistory{})

	service := NewGachaService(db)
	if err := service.InitializeGachaItems(); err != nil {
		t.Fatalf("failed to initialize gacha items: %v", err)
	}

	// Create a dummy user with sufficient gems for 10000 draws
	// 10000 * 300 = 3,000,000
	user := models.User{Name: "tester", Gem: 3000000}
	db.Create(&user)

	trials := 10000
	counts := make(map[string]int)

	for i := 0; i < trials; i++ {
		item, err := service.DrawGacha(user.ID)
		if err != nil {
			t.Fatalf("failed to draw gacha at iteration %d: %v", i, err)
		}
		counts[item.Rarity]++
	}

	expectedProbabilities := map[string]float64{
		"N":   0.5,
		"R":   0.3,
		"SR":  0.15,
		"SSR": 0.05,
	}

	tolerance := 0.02 // 2% tolerance

	for rarity, expected := range expectedProbabilities {
		actualCount := counts[rarity]
		actualProb := float64(actualCount) / float64(trials)

		if actualProb < expected-tolerance || actualProb > expected+tolerance {
			t.Errorf("Probability for %s out of range: expected %.2f, got %.4f", rarity, expected, actualProb)
		} else {
			t.Logf("Rarity %s: count=%d, probability=%.4f (expected %.2f)", rarity, actualCount, actualProb, expected)
		}
	}
}
