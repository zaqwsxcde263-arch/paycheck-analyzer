package com.paycheck.paycheckanalyzerapi.spending;

import com.paycheck.paycheckanalyzerapi.spending.dto.SpendingDto;
import com.paycheck.paycheckanalyzerapi.spending.dto.SpendingRequest;
import com.paycheck.paycheckanalyzerapi.user.User;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/spendings")
public class SpendingController {

    private final SpendingService spendingService;

    public SpendingController(SpendingService spendingService) {
        this.spendingService = spendingService;
    }

    @GetMapping
    public ResponseEntity<List<SpendingDto>> getSpendings(
            @AuthenticationPrincipal User user,
            @RequestParam(required = false) String month,
            @RequestParam(required = false) Long categoryId,
            @RequestParam(required = false, defaultValue = "date") String sort,
            @RequestParam(required = false, defaultValue = "desc") String order,
            @RequestParam(required = false) Integer limit) {
        List<SpendingDto> spendings =
                spendingService.getSpendings(user, month, categoryId, sort, order, limit);
        return ResponseEntity.ok(spendings);
    }

    @GetMapping("/{id}")
    public ResponseEntity<SpendingDto> getSpending(
            @AuthenticationPrincipal User user, @PathVariable Long id) {
        SpendingDto spending = spendingService.getSpending(user, id);
        return ResponseEntity.ok(spending);
    }

    @PostMapping
    public ResponseEntity<SpendingDto> createSpending(
            @AuthenticationPrincipal User user, @Valid @RequestBody SpendingRequest request) {
        SpendingDto created = spendingService.createSpending(user, request);
        return ResponseEntity.status(HttpStatus.CREATED).body(created);
    }

    @PutMapping("/{id}")
    public ResponseEntity<SpendingDto> updateSpending(
            @AuthenticationPrincipal User user,
            @PathVariable Long id,
            @Valid @RequestBody SpendingRequest request) {
        SpendingDto updated = spendingService.updateSpending(user, id, request);
        return ResponseEntity.ok(updated);
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteSpending(
            @AuthenticationPrincipal User user, @PathVariable Long id) {
        spendingService.deleteSpending(user, id);
        return ResponseEntity.noContent().build();
    }
}

