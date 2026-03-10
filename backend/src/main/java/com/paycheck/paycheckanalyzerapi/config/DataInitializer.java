package com.paycheck.paycheckanalyzerapi.config;

import com.paycheck.paycheckanalyzerapi.category.Category;
import com.paycheck.paycheckanalyzerapi.category.CategoryRepository;
import jakarta.annotation.PostConstruct;
import java.util.List;
import org.springframework.stereotype.Component;

@Component
public class DataInitializer {

    private final CategoryRepository categoryRepository;

    public DataInitializer(CategoryRepository categoryRepository) {
        this.categoryRepository = categoryRepository;
    }

    @PostConstruct
    public void initCategories() {
        if (categoryRepository.count() > 0) {
            return;
        }
        List<Category> categories = List.of(
                build("Groceries", "#4CAF50"),
                build("Dining", "#FF9800"),
                build("Transport", "#2196F3"),
                build("Entertainment", "#E91E63"),
                build("Utilities", "#9E9E9E"),
                build("Shopping", "#3F51B5"),
                build("Health", "#8BC34A"),
                build("Other", "#795548"));
        categoryRepository.saveAll(categories);
    }

    private Category build(String name, String color) {
        Category c = new Category();
        c.setName(name);
        c.setColor(color);
        return c;
    }
}

