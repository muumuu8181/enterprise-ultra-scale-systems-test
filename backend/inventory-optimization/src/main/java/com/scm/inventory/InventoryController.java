package com.scm.inventory;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import java.util.HashMap;
import java.util.Map;

@RestController
public class InventoryController {

    @GetMapping("/inventory/check")
    public Map<String, Object> checkInventory() {
        Map<String, Object> response = new HashMap<>();
        response.put("status", "ok");
        response.put("message", "Inventory service is running");
        response.put("items_count", 100);
        return response;
    }
}
