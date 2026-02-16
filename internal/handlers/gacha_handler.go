package handlers

import (
	"gacha-system/internal/services"
	"net/http"

	"github.com/gin-gonic/gin"
)

type GachaHandler struct {
	gachaService *services.GachaService
}

func NewGachaHandler(gachaService *services.GachaService) *GachaHandler {
	return &GachaHandler{gachaService: gachaService}
}

type DrawRequest struct {
	UserID uint `json:"user_id" binding:"required"`
}

func (h *GachaHandler) Draw(c *gin.Context) {
	var req DrawRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	item, err := h.gachaService.DrawGacha(req.UserID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, item)
}
