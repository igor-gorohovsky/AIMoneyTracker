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
    user_tg_id, currency_id
) VALUES (
    $1, $2
)
RETURNING *;

-- name: GetUser :one
SELECT * FROM user_account
WHERE user_tg_id = $1;

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
