-- name: CreateCurrency :one
INSERT INTO currency(
    name, iso_code, symbol
) VALUES (
    $1, $2, $3
)
RETURNING *;

-- name: GetCurrency :one
SELECT * FROM currency
WHERE iso_code = $1;

-- name: CreateUser :one
INSERT INTO user_account(
    currency_id
) VALUES (
    $1
)
RETURNING *;

-- name: GetUser :one
SELECT * FROM user_account
WHERE user_id = $1;

-- name: GetAccounts :many
SELECT * FROM account
WHERE user_id = $1;

-- name: CreateAccount :one
INSERT INTO account(
    user_id, name, balance, currency_id
) VALUES (
    $1, $2, $3, $4
)
RETURNING *;

-- name: CreateCategory :one
INSERT INTO category(
    user_id, name, type
) VALUES (
    $1, $2, $3
)
RETURNING *;

-- name: GetUserCategories :many
SELECT * FROM category
WHERE user_id = $1;

-- name: CreateRate :one
INSERT INTO rate(
    from_currency, to_currency, rate
) VALUES (
    $1, $2, $3
)
RETURNING *;

-- name: GetRate :one
SELECT * FROM rate
WHERE from_currency = $1 AND to_currency = $2;

-- name: UpdateRate :one
UPDATE rate
SET rate = $3
WHERE from_currency = $1 AND to_currency = $2
RETURNING *;

-- name: UpdateCategory :one
UPDATE category
SET name = $2
WHERE category_id = $1
RETURNING *;

-- name: GetCategoryById :one
SELECT * FROM category
WHERE category_id = $1 AND user_id = $2;

-- name: GetCategoryByName :one
SELECT * FROM category
WHERE name = $1 AND user_id = $2;

-- name: CreateTransaction :one
INSERT INTO transaction(
    user_id, account_id, category_id, withdrawal_amount, expense_amount, note, state, date, original_transaction_id
) VALUES (
    $1, $2, $3, $4, $5, $6, $7, $8, $9
)
RETURNING *;

-- name: GetTransactions :many
SELECT *
FROM transaction
WHERE user_id = $1
ORDER BY date DESC;

-- name: GetTransactionById :one
SELECT *
FROM transaction
WHERE transaction_id = $1 AND user_id = $2;

-- name: GetAccountByName :one
SELECT *
FROM account
WHERE user_id = $1 AND name = $2;

-- name: UpdateAccountBalance :one
UPDATE account
SET balance = $2
WHERE account_id = $1
RETURNING *;

-- name: GetAccountById :one
SELECT *
FROM account
WHERE account_id = $1;

-- name: UpdateTransaction :one
UPDATE transaction
SET account_id = $2,
    category_id = $3,
    withdrawal_amount = $4,
    expense_amount = $5,
    note = $6,
    date = $7,
    original_transaction_id = $9
WHERE transaction_id = $1 AND user_id = $8
RETURNING *;
