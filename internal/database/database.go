package database

import (
	"context"
	"database/sql"
	"fmt"

	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
	"gorm.io/gorm/schema"
)

// Open returns a configured GORM connection using the supplied DSN.
func Open(dsn string) (*gorm.DB, error) {
	cfg := &gorm.Config{
		Logger: logger.Default.LogMode(logger.Warn),
		NamingStrategy: schema.NamingStrategy{
			SingularTable: true,
		},
	}

	db, err := gorm.Open(postgres.Open(dsn), cfg)
	if err != nil {
		return nil, fmt.Errorf("open database: %w", err)
	}
	return db, nil
}

// MustOpen panics when the database connection cannot be established.
func MustOpen(dsn string) *gorm.DB {
	db, err := Open(dsn)
	if err != nil {
		panic(err)
	}
	return db
}

// SQLDB extracts the underlying *sql.DB handle.
func SQLDB(db *gorm.DB) (*sql.DB, error) {
	return db.DB()
}

// Close closes the underlying sql.DB connection.
func Close(db *gorm.DB) error {
	sqlDB, err := SQLDB(db)
	if err != nil {
		return err
	}
	return sqlDB.Close()
}

// PingContext performs a health check against the database.
func PingContext(ctx context.Context, db *gorm.DB) error {
	sqlDB, err := SQLDB(db)
	if err != nil {
		return err
	}
	return sqlDB.PingContext(ctx)
}
