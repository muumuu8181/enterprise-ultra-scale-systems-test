package main

import (
	"gacha-system/internal/handlers"
	"gacha-system/internal/models"
	"gacha-system/internal/services"
	"log"

	"github.com/gin-gonic/gin"
	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
)

func main() {
	db, err := gorm.Open(sqlite.Open("gacha.db"), &gorm.Config{})
	if err != nil {
		log.Fatal("failed to connect database")
	}

	// Migrate the schema
	db.AutoMigrate(&models.User{}, &models.GachaItem{}, &models.GachaHistory{})

	userService := services.NewUserService(db)
	userHandler := handlers.NewUserHandler(userService)

	gachaService := services.NewGachaService(db)
	gachaHandler := handlers.NewGachaHandler(gachaService)

	// Initialize gacha items
	if err := gachaService.InitializeGachaItems(); err != nil {
		log.Printf("failed to initialize gacha items: %v", err)
	}

	r := gin.Default()

	r.POST("/register", userHandler.Register)
	r.GET("/me", userHandler.GetMe)
	r.POST("/gacha", gachaHandler.Draw)

	r.Run(":8080")
}
