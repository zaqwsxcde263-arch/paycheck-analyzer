package com.paycheck.paycheckanalyzerapi.category;

import com.paycheck.paycheckanalyzerapi.category.dto.CategoryDto;
import com.paycheck.paycheckanalyzerapi.category.dto.CreateCategoryRequest;
import com.paycheck.paycheckanalyzerapi.user.User;
import java.util.List;
import java.util.stream.Collectors;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class CategoryService {

    private final CategoryRepository categoryRepository;

    public CategoryService(CategoryRepository categoryRepository) {
        this.categoryRepository = categoryRepository;
    }

    @Transactional(readOnly = true)
    public List<CategoryDto> getCategoriesForUser(User user) {
        return categoryRepository.findAllForUserOrGlobal(user).stream()
                .map(CategoryDto::fromEntity)
                .collect(Collectors.toList());
    }

    @Transactional
    public CategoryDto createCustomCategory(User user, CreateCategoryRequest request) {
        Category category = new Category();
        category.setUser(user);
        category.setName(request.getName());
        category.setColor(request.getColor());
        categoryRepository.save(category);
        return CategoryDto.fromEntity(category);
    }
}

