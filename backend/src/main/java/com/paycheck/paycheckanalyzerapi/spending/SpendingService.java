package com.paycheck.paycheckanalyzerapi.spending;

import com.paycheck.paycheckanalyzerapi.category.Category;
import com.paycheck.paycheckanalyzerapi.category.CategoryRepository;
import com.paycheck.paycheckanalyzerapi.spending.dto.SpendingDto;
import com.paycheck.paycheckanalyzerapi.spending.dto.SpendingRequest;
import com.paycheck.paycheckanalyzerapi.user.User;
import java.time.LocalDate;
import java.time.YearMonth;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.Optional;
import java.util.stream.Collectors;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class SpendingService {

    private final SpendingRepository spendingRepository;
    private final CategoryRepository categoryRepository;

    public SpendingService(SpendingRepository spendingRepository, CategoryRepository categoryRepository) {
        this.spendingRepository = spendingRepository;
        this.categoryRepository = categoryRepository;
    }

    @Transactional(readOnly = true)
    public List<SpendingDto> getSpendings(
            User user,
            String month,
            Long categoryId,
            String sort,
            String order,
            Integer limit) {

        LocalDate from;
        LocalDate to;
        if (month != null && !month.isEmpty()) {
            YearMonth ym = YearMonth.parse(month);
            from = ym.atDay(1);
            to = ym.atEndOfMonth();
        } else {
            YearMonth ym = YearMonth.now();
            from = ym.atDay(1);
            to = ym.atEndOfMonth();
        }

        String sortField = (sort == null || sort.isEmpty()) ? "date" : sort.toLowerCase(Locale.ROOT);
        Sort.Direction direction =
                (order != null && order.equalsIgnoreCase("asc")) ? Sort.Direction.ASC : Sort.Direction.DESC;
        Sort springSort;
        if ("amount".equals(sortField)) {
            springSort = Sort.by(direction, "amount");
        } else if ("category".equals(sortField)) {
            springSort = Sort.by(direction, "category.name");
        } else {
            springSort = Sort.by(direction, "date");
        }

        int pageSize = Optional.ofNullable(limit).filter(l -> l > 0).orElse(50);
        Pageable pageable = PageRequest.of(0, pageSize, springSort);

        List<Spending> spendings = spendingRepository.search(user, from, to, categoryId, pageable);
        return spendings.stream().map(SpendingDto::fromEntity).collect(Collectors.toList());
    }

    @Transactional(readOnly = true)
    public SpendingDto getSpending(User user, Long id) {
        Spending spending = spendingRepository.findByIdAndUser(id, user)
                .orElseThrow(() -> new IllegalArgumentException("Spending not found"));
        return SpendingDto.fromEntity(spending);
    }

    @Transactional
    public SpendingDto createSpending(User user, SpendingRequest request) {
        Category category = categoryRepository.findById(request.getCategoryId())
                .orElseThrow(() -> new IllegalArgumentException("Category not found"));

        Spending spending = new Spending();
        spending.setUser(user);
        applyRequest(spending, request, category);
        spendingRepository.save(spending);
        return SpendingDto.fromEntity(spending);
    }

    @Transactional
    public SpendingDto updateSpending(User user, Long id, SpendingRequest request) {
        Spending spending = spendingRepository.findByIdAndUser(id, user)
                .orElseThrow(() -> new IllegalArgumentException("Spending not found"));
        Category category = categoryRepository.findById(request.getCategoryId())
                .orElseThrow(() -> new IllegalArgumentException("Category not found"));

        applyRequest(spending, request, category);
        return SpendingDto.fromEntity(spending);
    }

    @Transactional
    public void deleteSpending(User user, Long id) {
        Spending spending = spendingRepository.findByIdAndUser(id, user)
                .orElseThrow(() -> new IllegalArgumentException("Spending not found"));
        spendingRepository.delete(spending);
    }

    private void applyRequest(Spending spending, SpendingRequest request, Category category) {
        spending.setProductName(request.getProductName());
        spending.setAmount(request.getAmount());
        spending.setSeller(request.getSeller());
        spending.setDate(request.getDate());
        spending.setCategory(category);
        spending.setNotes(request.getNotes());
        LocalDate date = request.getDate();
        if (spending.getCreatedAt() == null) {
            spending.setCreatedAt(date.atStartOfDay().atOffset(java.time.ZoneOffset.UTC));
        }
        spending.setUpdatedAt(LocalDate.now().atStartOfDay().atOffset(java.time.ZoneOffset.UTC));
    }
}

