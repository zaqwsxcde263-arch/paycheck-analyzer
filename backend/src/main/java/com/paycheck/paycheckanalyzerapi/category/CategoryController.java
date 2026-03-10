package com.paycheck.paycheckanalyzerapi.category;

import com.paycheck.paycheckanalyzerapi.category.dto.CategoryDto;
import com.paycheck.paycheckanalyzerapi.category.dto.CreateCategoryRequest;
import com.paycheck.paycheckanalyzerapi.user.User;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/categories")
public class CategoryController {

    private final CategoryService categoryService;

    public CategoryController(CategoryService categoryService) {
        this.categoryService = categoryService;
    }

    @GetMapping
    public ResponseEntity<List<CategoryDto>> getCategories(@AuthenticationPrincipal User user) {
        List<CategoryDto> categories = categoryService.getCategoriesForUser(user);
        return ResponseEntity.ok(categories);
    }

    @PostMapping
    public ResponseEntity<CategoryDto> createCategory(
            @AuthenticationPrincipal User user, @Valid @RequestBody CreateCategoryRequest request) {
        CategoryDto created = categoryService.createCustomCategory(user, request);
        return ResponseEntity.status(HttpStatus.CREATED).body(created);
    }
}

