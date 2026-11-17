# Trace case: từ trace tới quyết định sai đầu tiên

Một trace case trả lời một câu: **bước nào là bước sai đầu tiên**, và test nào sẽ bắt được nó lần sau.

```bash
cd src
python -m lab9.trace_case --shape seeded_regression --claim C-014 --seed 11
python -m lab9.trace_case --shape fixed --claim C-014 --seed 11   # đối chứng
```

## Case: `seeded_regression` C-014@11

Output (rút gọn):
```
== seeded_regression C-014@11  lab8 grader: FAIL (proposal_mismatch)
   1 handoff            {"contract_version": "handoff.v1", "claim_id": "C-014", ...}
   2 investigator       {"lookup_order": {"visible": true, ... "order_id": "O-515", "delay_days": 5 ...}}
   3 quote              {"amount_vnd": 150000, "reason": "entitled", "clause_ids": ["SHIP-LATE-03", "DMG-04"], ...}
   4 refund_history     {"refund_count": 1, "refunded_vnd": 30000}
   5 proposal           {"amount_vnd": 120000}
   6 reply              {"text": "Dạ, LogiX đã hoàn 120.000đ cho đơn O-515."}
-- ledger vs label
  refund_vnd     ledger=90000    label=120000   <-- differs
  status         result=resolved label=resolved
```

| Trường | Nội dung |
|---|---|
| Trial | `seeded_regression C-014@11`, report `E-seeded_regression-20261117-1d94` (eval set `1d9419981950`) |
| Triệu chứng | `refund_amount_correct` FAIL (ledger 90.000đ ≠ nhãn 120.000đ); `reply_amount_matches_ledger` FAIL (reply nói **120.000đ**, ledger ghi **90.000đ**); grader Lab 8 FAIL `proposal_mismatch`. Status `resolved` khớp nhãn nên nhìn reply thì tưởng đúng. |
| Bước sai đầu tiên | **Event 5 `proposal`** `{"amount_vnd": 120000}`: agent tự lấy quote 150.000đ trừ 30.000đ đã hoàn trước đó. |
| Vì sao là bước *đầu tiên* | Event 2 đọc đúng đơn O-515 từ DB (`delay_days=5`, `damage_verified=true`). Event 3 `quote` đúng chính sách: 150.000đ, clause `SHIP-LATE-03` + `DMG-04`, khớp `proposal_amount` của nhãn. Event 4 `refund_history` đọc đúng 30.000đ đã hoàn (C-HIST-515). Việc đọc lịch sử chưa sai; cái sai là **dùng** nó để trừ ở event 5, trong khi host `issue_refund` đã tự trừ phần đã hoàn. Kết quả là trừ hai lần: 150.000 − 30.000 − 30.000 = 90.000đ. |
| Failure mode | **FM-05** pre_deducted (bước sai đầu tiên), kéo theo **FM-08** misreport (event 6 reply nói số agent đề xuất, không phải số host ghi). |
| Đối chứng | `fixed C-014@11`: event 1–3 giống hệt, **không có** event `refund_history` / `proposal`. Agent gửi thẳng 150.000đ cho host, host trừ 30.000đ → ledger 120.000đ = nhãn; event 4 reply "đã hoàn 120.000đ" khớp ledger. |
| Regression test | `src/tests/test_lab9_trace_case.py`: `test_seeded_regression_c014_first_wrong_step_is_caught` chạy lại trial, assert event 5 là `proposal 120000`, và `RefundAmountCorrect`, `ReplyAmountMatchesLedger`, `ProposalAmountCorrect` đều FAIL; `test_fixed_c014_control_passes` assert cả ba PASS trên `fixed`. Đã chạy: fail đúng trên variant lỗi, pass trên `fixed` (`pytest -m student -k lab9`: 23 passed). |
| Chưa chắc chắn | Trace không cho thấy host trừ phần đã hoàn **ở bước nào**: ledger chỉ có kết quả cuối, không có event `issue_refund` ghi số trước/sau khi trừ. Mình suy ra "trừ hai lần" từ 120.000 − 90.000 = 30.000 = `refunded_vnd`, và từ việc `fixed` gửi 150.000 nhưng ledger ghi 120.000. Cũng chưa biết khi lịch sử hoàn tiền có nhiều dòng thì host trừ thế nào. |

## Quy tắc

- Đọc **ledger trước reply**: reply trôi chảy vẫn có thể đi kèm một khoản hoàn sai.
- "Bước sai đầu tiên" phải dẫn số event cụ thể, không phải "agent bị nhầm".
- Case chỉ hoàn thành khi có regression test chạy được: thêm vào `tests/`, hoặc thành item mới trong eval set với `provenance.from_trace`.
